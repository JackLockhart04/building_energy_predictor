### Project Overview

Traditional linear models often fail to predict energy spikes because HVAC systems typically operate on threshold based logic rather than steady state changes. This project implements an XGBoost ensemble regressor that captures these complex interactions, achieving a 18.5% NMAE, significantly outperforming the 64.9% NMAE of a Linear Regression baseline.

# Hosted on Github Pages

https://jacklockhart04.github.io/building_energy_predictor/

### Repository Structure

notebooks/: Contains the data cleaning, feature engineering, and model training workflows.  
models/: Saved XGBoost model files and linear regression model. 
frontend/: Code for the FastAPI based interactive dashboard and local deployment.  
requirements.txt: List of necessary Python libraries for reproduction.
Data is not included because of size. Can be aquired at https://www.kaggle.com/datasets/claytonmiller/buildingdatagenomeproject2

### Installation and Environment Setup

git is https://github.com/JackLockhart04/building_energy_predictor

### Libraries

Saved in requirements.txt
pip install -r requirements.txt

# Run demo

### Frontend

Must open frontend/index.html with a web host. I used live server extension in VSCode. Just double clicking to open doesn't work.

### Backend

Must have environment setup.
Must be in prediction dir.
Run main.py with python