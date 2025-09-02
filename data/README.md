# Brand/Generic Name Mapping

This directory contains Excel files with brand name to generic name mappings for enhanced drug identification.

## File Format

The system automatically detects and loads any `.xlsx` or `.xls` files in this directory.

### Required Columns

Your Excel file should contain these columns (case-insensitive):

- **brand_name** or **brand** or **Brand Name**: The brand/trade name of the drug
- **generic_name** or **generic** or **Generic Name**: The generic/chemical name of the drug

### Example Excel Content

| brand_name | generic_name |
|------------|--------------|
| Keflex     | cephalexin   |
| Amoxil     | amoxicillin  |
| Zithromax  | azithromycin |
| Cipro      | ciprofloxacin|
| Levaquin   | levofloxacin |

## How It Works

1. The system loads all Excel files in this directory on startup
2. Creates bidirectional mappings (brand → generic and generic → brand)
3. Uses fuzzy matching for partial name matches
4. Enhances RX-NORM search by suggesting related drug names
5. Improves drug identification accuracy

## Benefits

- **Better Drug Matching**: Finds drugs even when prescription uses different naming conventions
- **Cross-Reference Validation**: Verifies drug identifications against multiple sources
- **Enhanced Search**: Provides additional search terms for RX-NORM queries
- **Pharmacy Integration**: Supports your existing pharmacy drug database

## File Naming

Use descriptive names for your Excel files:
- `brand_generic_mapping.xlsx`
- `pharmacy_drug_database.xlsx`
- `medication_mappings.xlsx`

The system will load all valid Excel files found in this directory.
