"""
Step 1: Tweak Extraction & Parsing

This module extracts structured modifications from review text using LLM processing.
It converts natural language descriptions of recipe changes into structured
ModificationObject instances.
"""

import json
import os
from typing import Optional

from loguru import logger
from openai import OpenAI
from pydantic import ValidationError

from .models import ModificationList, ModificationObject, Recipe, Review
from .prompts import build_simple_prompt


class TweakExtractor:
    """Extracts structured modifications from review text using LLM processing."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the TweakExtractor.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use for extraction
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        logger.info(f"Initialized TweakExtractor with model: {model}")

    def extract_modification(
        self,
        review: Review,
        recipe: Recipe,
        max_retries: int = 3,
    ) -> list[ModificationObject]:
        """
        Extract ALL structured modifications from a review.

        A single review may contain multiple discrete modifications (e.g.,
        "I added an egg AND halved the sugar" = 2 modifications).

        Args:
            review: Review object containing modification text
            recipe: Original recipe being modified
            max_retries: Number of retry attempts if parsing fails (default: 3 per NFR-002)

        Returns:
            List of ModificationObject instances (empty list if extraction failed)
        """
        if not review.has_modification:
            logger.warning("Review has no modification flag set")
            return []

        # Build the prompt - use simple prompt to avoid format string issues
        prompt = build_simple_prompt(
            review.text, recipe.title, recipe.ingredients, recipe.instructions
        )

        logger.debug(
            "Extracting modifications from review: {}...".format(review.text[:100])
        )

        raw_output = None
        modification_data = None

        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1,  # Low temperature for consistent extractions
                    max_tokens=2000,  # Increased for multiple modifications
                )

                raw_output = response.choices[0].message.content
                logger.debug(f"LLM raw output: {raw_output}")

                # Check if we got a response
                if not raw_output:
                    logger.warning(f"Attempt {attempt + 1}: Empty response from LLM")
                    continue

                # Parse JSON response
                modification_data = json.loads(raw_output)

                # Handle both array format and single-object format (wrap in array)
                modifications = self._parse_modifications(modification_data)

                if modifications:
                    for mod in modifications:
                        logger.info(
                            f"Extracted {mod.modification_type} modification "
                            f"with {len(mod.edits)} edits"
                        )
                    logger.info(f"Total modifications extracted: {len(modifications)}")
                else:
                    logger.info("No actionable modifications found in review")

                return modifications

            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt + 1}: Failed to parse JSON: {e}")
                if attempt == max_retries:
                    logger.error(f"Max retries reached. Raw output: {raw_output}")

            except ValidationError as e:
                logger.warning(f"Attempt {attempt + 1}: Validation error: {e}")
                if attempt == max_retries:
                    logger.error(
                        f"Max retries reached. Invalid data: {modification_data}"
                    )

            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Unexpected error: {e}")
                if attempt == max_retries:
                    return []

        return []

    def _parse_modifications(self, data: dict) -> list[ModificationObject]:
        """
        Parse modification data with robust handling of different formats.

        Handles:
        - New array format: {"modifications": [...]}
        - Legacy single-object format: {"modification_type": ..., "edits": ...}

        Args:
            data: Parsed JSON data from LLM

        Returns:
            List of validated ModificationObject instances
        """
        modifications = []

        # Check for new array format
        if "modifications" in data:
            mod_list = data["modifications"]
            if isinstance(mod_list, list):
                for mod_data in mod_list:
                    try:
                        mod = ModificationObject(**mod_data)
                        modifications.append(mod)
                    except ValidationError as e:
                        logger.warning(f"Skipping invalid modification: {e}")
                return modifications
            else:
                logger.warning("'modifications' key exists but is not a list")

        # Fallback: wrap single object in array (legacy format compatibility)
        if "modification_type" in data and "edits" in data:
            logger.debug("Received legacy single-object format, wrapping in array")
            try:
                mod = ModificationObject(**data)
                return [mod]
            except ValidationError as e:
                logger.warning(f"Failed to parse legacy format: {e}")

        logger.warning(f"Unexpected data format: {list(data.keys())}")
        return []

    def extract_all_modifications(
        self,
        reviews: list[Review],
        recipe: Recipe,
        max_llm_calls: int = 10,
    ) -> list[tuple[ModificationObject, Review]]:
        """
        Extract ALL modifications from ALL reviews with has_modification=True.

        Reviews are processed in descending rating order for conflict resolution
        (highest-rated review's modifications are applied first).

        Args:
            reviews: List of reviews to process
            recipe: Original recipe being modified
            max_llm_calls: Maximum LLM calls per recipe (default: 10 per FR-009)

        Returns:
            List of (ModificationObject, source_Review) tuples for all extracted modifications
        """
        # Filter to reviews with modifications
        modification_reviews = [r for r in reviews if r.has_modification]

        if not modification_reviews:
            logger.warning("No reviews with modifications found")
            return []

        # Sort by rating descending (highest-rated first for conflict resolution)
        # Reviews without ratings go last
        modification_reviews.sort(
            key=lambda r: (r.rating is not None, r.rating or 0),
            reverse=True
        )

        logger.info(
            f"Processing {len(modification_reviews)} reviews with modifications "
            f"(max {max_llm_calls} LLM calls)"
        )

        all_modifications: list[tuple[ModificationObject, Review]] = []
        llm_calls_made = 0
        reviews_processed = 0
        reviews_skipped = 0

        for review in modification_reviews:
            if llm_calls_made >= max_llm_calls:
                reviews_skipped += 1
                logger.warning(
                    f"Skipping review (LLM call limit reached): {review.text[:50]}..."
                )
                continue

            logger.info(
                f"Processing review (rating={review.rating}): {review.text[:80]}..."
            )

            modifications = self.extract_modification(review, recipe)
            llm_calls_made += 1
            reviews_processed += 1

            for mod in modifications:
                all_modifications.append((mod, review))

            if modifications:
                logger.info(
                    f"Extracted {len(modifications)} modification(s) from review"
                )
            else:
                logger.info("No actionable modifications in review")

        logger.info(
            f"Extraction complete: {len(all_modifications)} total modifications "
            f"from {reviews_processed} reviews ({reviews_skipped} skipped due to limit)"
        )

        return all_modifications

    def extract_single_modification(
        self, reviews: list[Review], recipe: Recipe
    ) -> tuple[ModificationObject, Review] | tuple[None, None]:
        """
        DEPRECATED: Use extract_all_modifications() instead.

        Extract modification from a single randomly selected review.
        Kept for backward compatibility.
        """
        logger.warning(
            "extract_single_modification() is deprecated. "
            "Use extract_all_modifications() instead."
        )
        import random

        # Filter to reviews with modifications
        modification_reviews = [r for r in reviews if r.has_modification]

        if not modification_reviews:
            logger.warning("No reviews with modifications found")
            return None, None

        # Select one random review
        selected_review = random.choice(modification_reviews)
        logger.info(f"Selected review: {selected_review.text[:100]}...")

        modifications = self.extract_modification(selected_review, recipe)
        if modifications:
            logger.info("Successfully extracted modification from selected review")
            return modifications[0], selected_review
        else:
            logger.warning("Failed to extract modification from selected review")
            return None, None

    def test_extraction(
        self, review_text: str, recipe_data: dict
    ) -> Optional[ModificationObject]:
        """
        Test extraction with raw text and recipe data.

        Args:
            review_text: Raw review text
            recipe_data: Raw recipe dictionary

        Returns:
            ModificationObject if successful
        """
        review = Review(text=review_text, has_modification=True)
        recipe = Recipe(
            recipe_id=recipe_data.get("recipe_id", "test"),
            title=recipe_data.get("title", "Test Recipe"),
            ingredients=recipe_data.get("ingredients", []),
            instructions=recipe_data.get("instructions", []),
        )

        return self.extract_modification(review, recipe)
