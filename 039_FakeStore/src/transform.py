import logging
import pandas as pd

logger = logging.getLogger(__name__)


def transform_products(product_df):
    """Transforms raw product DataFrame by unnesting ratings, renaming columns,

    and enforcing standard data types.
    """
    if product_df.empty:
        logger.warning("Product DataFrame is empty. Skipping transformation.")
        return product_df

    try:
        logger.info("Transforming products dataset...")
        df = product_df.copy()

        # Safely unnest dictionary rating column
        if "rating" in df.columns:
            df["rating_rate"] = df["rating"].apply(
                lambda x: x.get("rate") if isinstance(x, dict) else None
            )
            df["rating_count"] = df["rating"].apply(
                lambda x: x.get("count") if isinstance(x, dict) else None
            )

        # Standardize column naming
        df = df.rename(
            columns={
                "id": "product_id",
                "title": "product_title",
                "price": "product_price",
                "description": "product_description",
                "category": "product_category",
            }
        )

        selected_cols = [
            "product_id",
            "product_title",
            "product_price",
            "product_description",
            "product_category",
            "rating_rate",
            "rating_count",
        ]

        df = df[selected_cols]

        # Enforce numeric types
        df["product_price"] = pd.to_numeric(
            df["product_price"], errors="coerce"
        )
        df["rating_rate"] = pd.to_numeric(df["rating_rate"], errors="coerce")
        df["rating_count"] = pd.to_numeric(df["rating_count"], errors="coerce")

        logger.info("Product transformation completed successfully.")
        return df

    except KeyError as key_err:
        logger.error(
            f"Missing expected column during product transformation: {key_err}"
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error in product transformation: {e}")
        raise


def transform_users(user_df):
    """Transforms raw user DataFrame by unnesting address/name dictionaries,

    renaming columns, and standardizing attributes.
    """
    if user_df.empty:
        logger.warning("User DataFrame is empty. Skipping transformation.")
        return user_df

    try:
        logger.info("Transforming users dataset...")
        df = user_df.copy()

        # Unnest nested dict fields safely
        df["user_firstname"] = df["name"].apply(
            lambda x: x.get("firstname") if isinstance(x, dict) else None
        )
        df["user_lastname"] = df["name"].apply(
            lambda x: x.get("lastname") if isinstance(x, dict) else None
        )
        df["street"] = df["address"].apply(
            lambda x: x.get("street") if isinstance(x, dict) else None
        )
        df["city"] = df["address"].apply(
            lambda x: x.get("city") if isinstance(x, dict) else None
        )
        df["zipcode"] = df["address"].apply(
            lambda x: x.get("zipcode") if isinstance(x, dict) else None
        )

        df = df.rename(
            columns={
                "id": "user_id",
                "email": "user_email",
                "username": "user_name",
            }
        )

        selected_cols = [
            "user_id",
            "user_firstname",
            "user_lastname",
            "user_email",
            "user_name",
            "street",
            "city",
            "zipcode",
        ]

        df = df[selected_cols]

        logger.info("User transformation completed successfully.")
        return df

    except KeyError as key_err:
        logger.error(
            f"Missing expected column during user transformation: {key_err}"
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error in user transformation: {e}")
        raise