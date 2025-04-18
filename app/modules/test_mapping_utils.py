import pytest
from modules.mapping_utils import list_available_mappings, load_mapping, map_extracted_data_to_cell_ids
import os

def test_list_available_mappings():
    mappings = list_available_mappings()
    assert isinstance(mappings, dict)
    assert 'GIFI' in mappings  # Assumes GIFI_map.xlsx exists
    for name, path in mappings.items():
        assert os.path.exists(path)
        assert path.name.endswith('_map.xlsx')

def test_load_mapping_gifi():
    gifi_map = load_mapping('GIFI')
    assert isinstance(gifi_map, dict)
    assert len(gifi_map) > 0
    # Check expected columns
    for code, cell_id in gifi_map.items():
        assert isinstance(code, str)
        assert isinstance(cell_id, str)

def test_map_extracted_data_to_cell_ids():
    # Use a fake extracted data dict with known GIFI code from mapping
    gifi_map = load_mapping('GIFI')
    some_code = next(iter(gifi_map.keys()))
    cell_id = gifi_map[some_code]
    extracted = {some_code: '1234.56'}
    mapped = map_extracted_data_to_cell_ids(extracted, 'GIFI')
    assert cell_id in mapped
    assert mapped[cell_id] == '1234.56'

# Optionally, add tests for missing/invalid mapping files and codes
def test_missing_mapping_raises():
    import pytest
    with pytest.raises(FileNotFoundError):
        load_mapping('DOES_NOT_EXIST')

def test_invalid_mapping_structure(tmp_path):
    # Create a dummy mapping file with only one column
    import pandas as pd
    df = pd.DataFrame({'A': [1, 2, 3]})
    bad_map = tmp_path / 'BAD_map.xlsx'
    df.to_excel(bad_map, index=False)
    # Patch mapping dir to include this file
    from modules import mapping_utils
    orig_dir = mapping_utils.Path(mapping_utils.__file__).parent.parent / 'mapping'
    try:
        mapping_utils.Path = lambda *a, **kw: tmp_path if 'parent' in str(a) else orig_dir
        with pytest.raises(ValueError):
            load_mapping('BAD')
    finally:
        mapping_utils.Path = mapping_utils.Path.__class__
