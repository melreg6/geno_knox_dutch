# GenoKnoxDutch

A pipeline and web UI that extracts construct grammar from a GenoCAD database, translates it into Goldbar rules, submits those rules to a running Knox server, and enumerates the valid designs Knox returns in a format comatible with DoubleDutch.

---

# Setup & Run Instructions

## 1. Prerequisites

* Ensure **Python 3.9+** is installed.
* The Python standard library covers most dependencies.
* Install any additional dependencies listed in the `requirements.txt` file inside the `final_ui` folder.
* Note: `sqlite3` ships with Python by default, so no separate installation is required.

---

## 2. Knox Service

* The **Knox service must be running locally on port `8080` before starting the pipeline**.
* Knox is a **separate application** and is **not included in this repository**.
* You must install and launch Knox from its own source before continuing.

---

## 3. Database Setup

Run the following script once to build the database:

```bash
python convert_to_db.py
```

* This generates `genocad.db` from the MySQL dump.
* After creation, the database is reused for all future runs.

---

## 4. Running the Flask Application

### Step 1: Navigate to the UI directory

```bash
cd final_ui
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

### Step 3: Activate the virtual environment

* **Linux / macOS:**

```bash
source venv/bin/activate
```

* **Windows (PowerShell):**

```bash
venv\Scripts\activate
```

---

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5: Run the application

```bash
python app.py
```

* After running, **CTRL + click** the URL displayed in the terminal to open the app in your browser.

---

## 5. Using the Application

* Open the generated HTML page in your browser.
* Select genetic parts and constraints.
* The proxy system will:

  * Route requests through Knox
  * Return enumerated genetic designs

---

## 6. Running Tests

Navigate to the **test** directory, and run:

```bash
pytest
```
If it does not work, ensure you have pytest installed:
```bash
pip install pytest
```
### Important Note:

* `test_known_designs.py` requires the rebuilt database.
* You **must run `convert_to_db.py` first** before executing tests.


## Team

Varsha Athreya · Melissa Regalado · Paulina Garcia · Denalda Gashi
