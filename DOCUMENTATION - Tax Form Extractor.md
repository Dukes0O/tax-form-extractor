# Tax Form Extractor - Project Documentation

## Project Overview

The Tax Form Extractor is an application designed to process tax documents (PDFs and DOCX files), extract relevant financial data, map it to GIFI (General Index of Financial Information) codes, and generate CSV files for tax preparation software. The system now includes support for user-defined save locations and multiple extraction workflows for different tax schedules and formats.

## Key Components

### 1. Main Application (`main.py`)

- Flask-based web application with routes for file upload, processing, and CSV generation
- Handles both PDF and DOCX file formats
- Integrates with OpenAI's Vision API for data extraction from images
- Supports page selection for PDF documents
- Supports user-defined save directories for CSV output
- Provides modular workflow selection for different extraction needs
- Supports multiple tax form dictionaries for flexible data extraction

### 2. Mapping Module (`mapping_utils.py`)

- Loads GIFI code mappings from an Excel file (`GIFI_map.xlsx`)
- Maps extracted data to cell IDs based on GIFI codes
- Provides utility functions for data transformation and mapping
- Supports multiple dictionaries for different tax forms and schedules

### 3. CSV Generation (`csv_utils.py`)

- Generates CSV files from mapped data
- Formats output with cell IDs in column A and values in column B
- Saves CSV files to user-specified locations or defaults to the source directory

### 4. OpenAI Integration (`openai_utils.py`)

- Interfaces with OpenAI's Vision API (GPT-4o model)
- Processes images to extract financial data
- Uses specialized prompts to identify GIFI codes and values
- Supports modular extension for additional document processing needs

### 5. User Interface

- Web-based interface for uploading and processing tax forms
- Supports page selection for multi-page PDF documents
- Displays extraction results and provides CSV download
- Allows users to specify save locations for output files
- Supports selection of different processing workflows
- Future enhancement: Support for LAN hosting on a business network

## Project Blueprint: Enabling Multi‑Dictionary Workflows & Enhanced UI

### **Scope Summary**  
This initiative will evolve the existing single‑dictionary extractor (currently only GIFI) into a flexible, multi‑dictionary engine able to load and apply any user‑provided mapping (eg: GIFI, T2 Schedule 1, T661, Project Descriptions). It also introduces model configurability to switch to a lower‑cost OpenAI model, refines the UI to let users choose extraction workflows and models at runtime, and adds a one‑click startup mechanism so non‑technical users can launch the app without manual commands. Out of scope for now are wholesale redesigns of the AI prompt logic or migrating extraction entirely off OpenAI Vision—those can follow in later phases. Key risks include mapping‑file format inconsistencies, potential drop in extraction accuracy when switching models, and UI complexity creeping beyond a clean, intuitive interface.

### **Work‑Breakdown Structure**  
- **Epic: Multi-Dictionary Support**  
  - Refactor `mapping_utils` to accept a chosen dictionary identifier.  
  - Standardize dictionary files in a `mapping/` folder (e.g., `GIFI_map.xlsx`, `T2S1_map.xlsx`, `T661_map.xlsx`).  
  - Update loader logic to enumerate available maps and validate their structure.  
  - Write unit tests for each dictionary to confirm correct cell‑ID assignments.

- **Epic: Model Configuration**  
  - Abstract model name into configuration (`.env` or config file).  
  - Modify `openai_utils` to read the model setting and default to a cheaper tier (eg: `gpt-3.5-turbo`) if set.  
  - Expose model selection in the UI so users can switch per session.  
  - Run comparative tests on key forms to ensure mapping accuracy remains acceptable.

- **Epic: New Extraction Workflows**  
  - **T2 Schedule 1**: create `T2S1_map.xlsx`, define prompts (PDF → image path).  
  - **Project Description (DOCX)**: build a pure‑Python parser in `docx_utils`, plus a specialized OpenAI prompt for extracting narrative descriptions.  
  - **T661**: draft `T661_map.xlsx`, integrate into both PDF and DOCX pipelines.  
  - Ensure each workflow plugs into the same “extract → map → output” core.

- **Epic: UI & Startup Enhancements**  
  - Redesign `index.html` to include dropdowns for “Extraction Type” and “AI Model.”  
  - Add a mapping‑management panel (admin view) listing installed dictionaries with import/remove buttons.  
  - Implement a desktop‑friendly launcher script (`start.sh`/`start.bat`) or package via PyInstaller to spin up frontend and backend with one click.  
  - Validate UX flow: upload → choose pages and workflow → select model → run → download.

- **Epic: Testing, Documentation & Release**  
  - Expand test suite to cover all new workflows and model permutations.  
  - Update `DOCUMENTATION‑Tax Form Extractor.md` with usage for multi‑dictionary and model selection.  
  - Add troubleshooting notes for model‑switch errors and mapping file issues.  
  - Prepare a new release with updated changelog and version bump.

### **Architecture Sketch**  
All pipelines will feed into a shared core. At startup, the UI loads available dictionaries and models from a `config` service. When the user submits a job, the controller routes it through the selected extractor (PDF‑ or DOCX‑based), then invokes the mapping engine with the chosen dictionary, and finally hands off to CSV generation. A simplified component flow:

```
┌───────────────┐    ┌───────────────┐    ┌──────────────┐
│   Front End   │──▶ │   Controller  │──▶ │  Extractor   │
│ (Upload + UI) │    │ (routes tasks)│    │ (PDF/DOCX +  │
└───────────────┘    └───────────────┘    │  OpenAI API) │
                                              │
                                              ▼
                                         ┌────────────┐
                                         │  Mapper    │
                                         │ (multi‑dict)│
                                         └────────────┘
                                              │
                                              ▼
                                         ┌────────────┐
                                         │ CSV Writer │
                                         └────────────┘
```

### **Technology Choices**  
- **Mapping Storage** remains as Excel (`.xlsx`) for ease of authoring by tax SMEs; each sheet follows the same schema.  
- **Model Config** via environment variables (`.env`) so CI pipelines or local users can tweak cost vs accuracy.  
- **Packaging** with PyInstaller to bundle the Flask app and Poppler binaries into a double‑clickable executable on Windows/Mac.  
- **UI Framework** continues on Bootstrap, adding minimal JavaScript for dynamic dropdowns—no heavy SPA frameworks to keep maintenance light.  

### **Definition of Done**  
- User can pick any installed dictionary from the UI and see it applied correctly in sample runs.  
- Model dropdown actually alters which OpenAI model is called, and fallback works if the chosen model isn’t available.  
- New workflows for T2 S1, Project Description, and T661 run end‑to‑end without errors and pass automated tests.  
- A single desktop icon or script reliably starts both backend and frontend on target platforms.  
- Documentation and tests updated; all CI checks green.  

### **High‑Level Timeline**  
- **Week 1**: Core refactor for multi‑dictionary support & basic UI dropdown.  
- **Week 2**: Implement and test T2 S1 and T661 dictionaries; build DOCX parser for Project Descriptions.  
- **Week 3**: Model abstraction work and comparative accuracy tests; extend UI with model selector.  
- **Week 4**: Packaging work—scripts or PyInstaller build; user acceptance testing.  
- **Week 5**: Final polish: documentation updates, test coverage ramp‑up, release prep.

## Project Status and Milestones

### Current Status (March 12, 2025)

#### Completed Features

1. **PDF Processing**

   - Multi-page PDF support with selective page processing
   - Integration with Poppler for PDF to image conversion
   - Proper PATH and DLL handling for Windows systems

2. **User Interface**

   - File upload functionality
   - Page selection interface for multi-page PDFs
   - Real-time processing status updates
   - Error handling and user feedback
   - Save directory selection feature
   - Dropdown selection for different processing workflows

3. **Data Extraction**

   - OpenAI Vision API integration for image processing
   - GIFI code extraction from tax forms
   - Support for both PDF and DOCX file formats
   - Future support for non-API DOCX processing using native Python

4. **Error Handling and Logging**

   - Comprehensive error handling in both frontend and backend
   - Detailed logging system for debugging and monitoring
   - User-friendly error messages in the UI

## Milestones Achieved
### Recent Milestones

### Initial Setup and Development
- Created Flask application structure
- Implemented file upload and processing functionality
- Integrated with OpenAI's Vision API for data extraction

### GIFI Mapping Implementation
- Created mapping module to load GIFI codes from Excel file
- Implemented mapping logic to convert GIFI codes to cell IDs
- Updated main application to use the mapping functionality

### CSV Generation
- Implemented CSV generation with proper formatting
- Ensures cell IDs are in column A and values in column B

### Testing Environment Setup
- Created `requirements.txt` with all necessary dependencies
- Successfully installed all dependencies
- Documented installation process and requirements

### GIFI Mapping Testing
- Created comprehensive test scripts to validate mapping functionality
- Verified successful loading of GIFI mappings from Excel file
- Confirmed correct mapping of GIFI codes to cell IDs
- Validated handling of combined data from multiple pages
- All tests passed successfully with 698 GIFI mappings loaded and correctly mapped

### Enhanced User Interface and PDF Processing
- Implemented page selection functionality for PDF documents
- Created a responsive web interface with Bootstrap
- Added dynamic page checkbox generation for multi-page PDFs
- Implemented status indicators for processing steps

### OpenAI GPT-4o Integration
- Updated OpenAI utilities to use the GPT-4o model
- Enhanced prompt engineering for better GIFI code extraction
- Implemented proper error handling for API responses
- Added environment variable configuration for API key management

### Parenthetical Value Handling
- Implemented PDF text extraction to identify values in parentheses
- Created post-processing logic for exception codes and negative values
- Successfully tested with different tax form formats
- Achieved high accuracy in extracting and formatting GIFI values

## Testing Results

### GIFI Mapping Tests
- **Test Date**: March 12, 2025
- **Test Script**: `test_mapping_updated.py`
- **Results**:
  - Successfully loaded 698 GIFI mappings
  - Correctly mapped sample data to cell IDs
  - Successfully handled combined data from multiple pages
  - All tests passed with 100% accuracy

#### Sample Test Data
- Original test data: `{'1000': '10000.00', '1060': '5000.00', '3460': '2500.00'}`
- Mapped data: `{'GFGBA.Ttwgba62': '10000.00', 'GFGBA.Ttwgba71': '5000.00', 'GFGIB.Ttwgib34': '2500.00'}`

#### Combined Data Test
- Flattened data: `{'1000': '10000.00', '1060': '5000.00', '3460': '2500.00', '3470': '1200.00'}`
- Mapped data: `{'GFGBA.Ttwgba62': '10000.00', 'GFGBA.Ttwgba71': '5000.00', 'GFGIB.Ttwgib34': '2500.00', 'GFGIB.Ttwgib35': '1200.00'}`

### OpenAI Integration Tests
- **Test Date**: March 12, 2025
- **Test Script**: `test_openai_integration.py`
- **Results**:
  - Successfully extracted GIFI codes and values from different tax form formats
  - Properly handled parenthetical values and converted them to negative numbers
  - Correctly identified and processed exception GIFI codes that should remain positive
  - Achieved high mapping rates: 77% for standard format and 50% for alternative format

#### Parenthetical Value Handling
- Implemented PDF text extraction to identify values in parentheses
- Created post-processing logic to handle exception codes and convert parenthetical values to negative numbers
- Exception codes (e.g., accumulated amortization codes like 1741, 1743, 1775) are kept positive even when in parentheses
- Non-exception codes in parentheses are correctly converted to negative numbers

#### Format Compatibility
- **Test Case 1**: Standard tax form format (G100)
  - Extracted 31 GIFI codes with 77% mapping rate
  - Successfully identified and processed 5 parenthetical values
  - Correctly handled all exception codes

- **Test Case 2**: Alternative tax form format (SPARKGEO)
  - Extracted 24 GIFI codes with 50% mapping rate
  - Successfully handled different layout and formatting
  - Demonstrated format flexibility of the extraction system

## Next Steps

### **1. Multi-Dictionary Support**
   - Implement additional dictionaries for different tax schedules.
   - Allow users to select which dictionary to apply during extraction.

### **2. Expanded DOCX Processing**
   - Add **native Python extraction methods** for structured DOCX tax forms.
   - Develop **custom parsing logic** for different document layouts.

### **3. Workflow Expansion**
   - Define **specific extraction workflows** for tax schedules **T2, T4, etc.**.
   - Refine **UI for user selection** of workflows.

### **4. Performance Optimization**
   - Optimize **image processing** for faster extraction.
   - Implement **caching for frequently accessed data**.
   - Improve **response times for large documents**.

### **5. Business LAN Deployment**
   - Configure the application to be accessible over a **local business network** while hosted on a laptop.
   - Ensure **security and access controls** are in place.
   - **Test and optimize** networked access for multiple users.

## Usage Instructions

### **1. Running the Application**
#### **Step 1: Install Dependencies**
Ensure all dependencies are installed by running:
```bash
pip install -r requirements.txt
```

#### **Step 2: Set Up Environment Variables**
Create a `.env` file in the project directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

#### **Step 3: Start the Flask Application**
Run the main Python script:
```bash
python app/main.py
```
By default, the application will start on **http://localhost:5000**.

### **2. Using the Web Interface**
#### **Step 1: Upload a Tax Form**
- Open your browser and go to **http://localhost:5000**.
- Click the **"Upload Tax Form"** button.
- Select a **PDF or DOCX** file and submit.

#### **Step 2: Select Pages to Process (PDFs Only)**
- If a **PDF** is uploaded, the system will detect the number of pages.
- Check the boxes for the pages you want to process.
- Click **"Process Selected Pages"** to continue.

#### **Step 3: Choose a Workflow and Save Location**
- Select the appropriate **workflow** from the dropdown (e.g., T2, T4, DOCX processing).
- Specify the **save location** for the CSV file (or leave blank to save in the same directory as the uploaded file).

#### **Step 4: Process and Review Extracted Data**
- The system extracts GIFI codes and values from the selected pages.
- The extracted data and mapped results are displayed in the interface.

#### **Step 5: Download the CSV**
- Once processing is complete, click **"Download CSV"** to save the extracted data.

### **3. Testing the Application**
#### **Full End-to-End Test**
1. Upload a PDF or DOCX file.
2. Select the appropriate pages (PDF only).
3. Choose the correct workflow.
4. Specify the save location (or use default).
5. Process the document.
6. Validate that the CSV is correct.