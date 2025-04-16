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

    
def load_translations(self, excel_path):
    """
    Enhanced Excel parser with validation and normalization
    
    Args:
        excel_path (str): Path to the Excel file
    """
    try:
        # Try multiple encodings if needed
        try:
            df = pd.read_excel(excel_path)
        except UnicodeDecodeError:
            # Try different encodings
            df = pd.read_excel(excel_path, encoding='utf-8')
        
        # Validate the expected columns exist
        required_columns = ["Key", "Original EN", "Original CN", "Original KH", 
                            "KH Confirm from BIC", "CN Confirm from BIC"]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Clean and normalize data
        for col in df.columns:
            if df[col].dtype == 'object':  # String columns
                # Replace NaN with empty string
                df[col] = df[col].fillna('')
                # Trim whitespace
                df[col] = df[col].str.strip()
                # Normalize whitespace
                df[col] = df[col].apply(lambda x: re.sub(r'\s+', ' ', str(x)) if isinstance(x, str) else x)
                # Handle HTML entities
                df[col] = df[col].apply(lambda x: html.unescape(str(x)) if isinstance(x, str) else x)
        
        # Create search indexes for faster lookups
        df['en_lower'] = df['Original EN'].str.lower()
        df['kh_lower'] = df['KH Confirm from BIC'].str.lower()
        df['cn_lower'] = df['CN Confirm from BIC'].str.lower()
        
        # Check for duplicate keys and warn
        duplicate_keys = df[df.duplicated('Key')]['Key'].tolist()
        if duplicate_keys:
            logger.warning(f"Found duplicate keys in Excel: {duplicate_keys}")
            
        # Check for empty translations and warn
        for col in ["Original EN", "KH Confirm from BIC", "CN Confirm from BIC"]:
            empty_keys = df[df[col] == '']['Key'].tolist()
            if empty_keys:
                logger.warning(f"Found {len(empty_keys)} keys with empty {col} translations")
                
        logger.info(f"Successfully loaded {len(df)} translation entries")
        return df
    
    except Exception as e:
        logger.error(f"Failed to load translations: {str(e)}")
        raise