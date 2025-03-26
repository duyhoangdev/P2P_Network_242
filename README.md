P2P Network Project
This project implements a peer-to-peer (P2P) file-sharing system with a backend server and a frontend interface.
Prerequisites
Before you begin, ensure you have the following installed:
Python 3.8 or higher

Git

Setup Instructions
Follow these steps to download and set up the project on your local machine:
1. Download and Navigate to the Project
Assuming this is a GitHub repository, you can clone it using Git. Replace the URL with your actual repository URL if different.
bash

git clone <your-repository-url>
cd P2P_Network_242

2. Set Up a Virtual Environment for the Backend
A virtual environment ensures that dependencies are isolated from your system Python.
bash

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

3. Install Backend Dependencies
Navigate to the tracker directory and install the required libraries.
bash

cd tracker
pip install -r requirements.txt
cd ..

4. Set Up a Virtual Environment for the Frontend
For simplicity, you can reuse the same virtual environment unless separate environments are required. However, I’ll assume a new one for clarity as per your request.
Open a new terminal, navigate to the node directory, and set up a virtual environment:
bash

cd node
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

5. Install Frontend Dependencies
Still in the node directory, install the required libraries.
bash

pip install -r requirements.txt

Running the Application
To run the project, you need to start both the backend and frontend in separate terminals.
1. Start the Backend Server
In the first terminal, navigate to the tracker directory (if not already there) and run:
bash

cd tracker
uvicorn main:app --reload --host 0.0.0.0 --port 8000

--reload: Automatically reloads the server when code changes are detected (useful for development).

--host 0.0.0.0: Makes the server accessible from any IP address.

--port 8000: Runs the server on port 8000.

2. Start the Frontend Interface
In the second terminal, navigate to the node directory (if not already there) and run:
bash

cd node
streamlit run app.py

Streamlit will start the frontend, typically accessible at http://localhost:8501.

3. Access the Application
Backend API: Open your browser or a tool like Postman and go to http://localhost:8000.

Frontend Interface: Open your browser and go to http://localhost:8501 (default Streamlit port).

Additional Notes
Activating the Virtual Environment: Always ensure the virtual environment is activated before running pip or application commands. You’ll see (venv) in your terminal prompt when it’s active.

Single Virtual Environment Option: If you prefer, you can use one virtual environment for both backend and frontend by installing all dependencies into the same venv and skipping step 4. Adjust the steps accordingly.

Troubleshooting: 
If you get a ModuleNotFoundError, ensure all dependencies listed in requirements.txt are installed correctly.

If ports 8000 or 8501 are in use, change them using --port in the respective commands.

