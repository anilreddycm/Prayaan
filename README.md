# Prayaan

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)  
[![Python version](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org)

## About
Prayaan is a web‑application built to help manage travel-related data, streamline operations, and improve usability for users.

## Features
- User authentication  
- CRUD operations  
- Responsive UI  
- REST API support  
- Media upload support

## Technology Stack
| Layer        | Technologies |
|--------------|-------------|
| Backend      | Python, Django |
| Frontend     | HTML, CSS, JavaScript |
| Database     | SQLite |
| Others       | Shell/Python scripts |

## Installation
```bash
git clone https://github.com/NarendraReddy077/Prayaan.git
cd Prayaan
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the App
```bash
python manage.py migrate
python populate_cars.py
python manage.py runserver
```

## Project Structure
```
Prayaan/
├─ .github/workflows/
├─ app/
├─ media/
├─ manage.py
├─ populate_cars.py
├─ requirements.txt
└─ CAR_CRUD_CURL.md
```

## Contributing
1. Fork the repo  
2. Create a branch  
3. Commit changes  
4. Push and create a pull request  

## License
MIT License.

## Contact
**Narendra Reddy**  
GitHub: https://github.com/NarendraReddy077
