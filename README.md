# Fake Review Detector

## Overview
The Fake Review Detector is a machine learning application designed to identify and flag fake reviews using advanced natural language processing techniques. This project leverages TensorFlow and the Transformers library to build a robust model that can analyze text data and provide insights into the authenticity of reviews.

## Features
- **Machine Learning Model**: Utilizes TensorFlow and Transformers for effective review classification.
- **API Integration**: Built with Flask, allowing easy integration with other applications.
- **Cross-Origin Resource Sharing (CORS)**: Enabled for seamless API requests from different origins.
- **User-Friendly Extension**: A Chrome extension that allows users to flag reviews directly from their browser.

## Project Structure
```
├── app.py                  # Main application file
├── README.md               # Project documentation
├── requirements.txt        # Python package dependencies
├── backend/                # Backend services
│   ├── __init__.py        # Package initialization
│   ├── xai_service.py      # Explainable AI service
│   └── transformer.ipynb   # Jupyter notebook for model training
├── model/                  # Model artifacts
│   ├── added_tokens.json   # Tokenizer data
│   ├── config.json         # Model configuration
│   ├── special_tokens_map.json # Special tokens mapping
│   ├── spm.model           # SentencePiece model
│   ├── tf_model.h5        # Trained TensorFlow model
│   └── tokenizer_config.json # Tokenizer configuration
├── data/                   # Dataset files
│   └── fake_reviews_dataset.csv # Dataset for training and evaluation
└── extension/              # Chrome extension files
    ├── background.js       # Background script
    ├── content.js          # Content script
    ├── manifest.json       # Extension manifest
    └── popup/              # Popup UI files
        ├── popup.css       # Popup styles
        ├── popup.html      # Popup HTML
        └── popup.js        # Popup script
```

## Installation
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd fakeReviewDetector
   ```
2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application**:
   ```bash
   python app.py
   ```

## Usage
- To train the model, run:
  ```bash
  python train_model.py
  ```
- To use the Chrome extension, go to Chrome > Extensions > Load unpacked and select the `extension` folder.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- TensorFlow
- Hugging Face Transformers
- Flask
- The contributors of this project.
