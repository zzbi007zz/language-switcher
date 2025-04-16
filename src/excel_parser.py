def parse_excel_with_validation(excel_path):
    """
    Enhanced Excel parser with validation and normalization
    
    Args:
        excel_path (str): Path to the Excel file
        
    Returns:
        DataFrame: Processed translations dataframe
    """
    try:
        # Load the Excel file
        df = pd.read_excel(excel_path)
        
        # Validate the expected columns exist
        required_columns = ["Key", "Original EN", "Original CN", "Original KH", "KH Confirm from BIC", "CN Confirm from BIC"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Clean up data
        for col in df.columns:
            if df[col].dtype == 'object':  # String columns
                # Replace NaN with empty string
                df[col] = df[col].fillna('')
                # Trim whitespace
                df[col] = df[col].str.strip()
                # Normalize whitespace (replace multiple spaces with single space)
                df[col] = df[col].apply(lambda x: re.sub(r'\s+', ' ', str(x)) if isinstance(x, str) else x)
        
        # Validate keys are unique
        duplicate_keys = df[df.duplicated('Key')]['Key'].tolist()
        if duplicate_keys:
            logger.warning(f"Found duplicate keys in Excel: {duplicate_keys}")
        
        # Create additional search index for faster lookups
        df['en_lower'] = df['Original EN'].str.lower()
        df['kh_lower'] = df['KH Confirm from BIC'].str.lower()
        df['cn_lower'] = df['CN Confirm from BIC'].str.lower()
        
        logger.info(f"Successfully parsed Excel with {len(df)} translation entries")
        return df
    
    except Exception as e:
        logger.error(f"Error parsing Excel file: {str(e)}")
        raise