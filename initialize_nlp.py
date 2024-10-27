import spacy
import os

def download_spacy_model():
    try:
        # Try to load the model first
        try:
            nlp = spacy.load('en_core_web_sm')
            print("Model already installed")
            return True
        except OSError:
            pass
            
        # If loading fails, download the model
        spacy.cli.download("en_core_web_sm")
        # Verify installation
        nlp = spacy.load('en_core_web_sm')
        print("Successfully downloaded and installed spaCy model")
        return True
    except Exception as e:
        print(f"Error installing spaCy model: {str(e)}")
        return False

if __name__ == "__main__":
    download_spacy_model()
