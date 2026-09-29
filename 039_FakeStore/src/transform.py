import pandas as pd

def transform_products(product_df):
    """
    Transforms product data by flattening nested dictionaries,
    renaming columns, and formatting data types.
    """
    product_df = product_df.copy()
    
    # 1. Un-nest the 'rating' dictionary into separate columns
    if 'rating' in product_df.columns:
        product_df['rating_rate'] = product_df['rating'].apply(lambda x: x.get('rate') if isinstance(x, dict) else None)
        product_df['rating_count'] = product_df['rating'].apply(lambda x: x.get('count') if isinstance(x, dict) else None)

    # 2. Rename existing columns
    product_df = product_df.rename(columns={
        'id': 'product_id',
        'title': 'product_title',
        'price': 'product_price',
        'description': 'product_description',
        'category': 'product_category'
    })

    # 3. Explicitly select only flattened tabular columns (excluding raw dicts)
    selected_columns = [
        'product_id', 
        'product_title', 
        'product_price', 
        'product_description', 
        'product_category',
        'rating_rate',
        'rating_count'
    ]
    
    product_df = product_df[selected_columns]
    
    # 4. Ensure numeric types
    product_df['product_price'] = pd.to_numeric(product_df['product_price'], errors='coerce')
    product_df['rating_rate'] = pd.to_numeric(product_df['rating_rate'], errors='coerce')
    product_df['rating_count'] = pd.to_numeric(product_df['rating_count'], errors='coerce')

    return product_df  

def transform_users(user_df):
    """
    Transforms the user DataFrame by renaming columns and converting data types.

    Args:
        user_df (pd.DataFrame): The original user DataFrame.
        """
    #copy the dataframe to avoid modifying the original
    user_df = user_df.copy()
    # Example transformation: rename columns and convert data types
    user_df = user_df.copy()
    user_df['user_firstname'] = user_df['name'].apply(lambda x: x['firstname'])
    user_df['user_lastname'] = user_df['name'].apply(lambda x: x['lastname'])
    user_df['street'] = user_df['address'].apply(lambda x: x['street'])
    user_df['city'] = user_df['address'].apply(lambda x: x['city'])
    user_df['zipcode'] = user_df['address'].apply(lambda x: x['zipcode'])

    user_df = user_df.rename(columns={
        'id': 'user_id',
        'email': 'user_email',
        'username': 'user_name'
    })

    user_df = user_df[['user_id',
                        'user_firstname',
                        'user_lastname',
                        'user_email',
                        'user_name',
                        'street',
                        'city',
                        'zipcode']]

    return user_df