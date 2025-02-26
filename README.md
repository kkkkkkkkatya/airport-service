# Airplane Service REST API

## Description
The Airplane Service REST API is a web-based application that provides functionalities for managing airplane operations, including registration, flight tracking, and user management. It offers a robust and secure platform for users to interact with airplane data efficiently.


### **Test User Credentials**
To explore the platform without signing up, use the following test account:
- **Email:** `testuser@example.com`
- **Password:** `testpassword`

## Visuals
### API Documentation
You can find the interactive API documentation powered by Swagger at `http://127.0.0.1:8000/api/doc/swagger/`.

## Installation
### Requirements
- Docker
- Docker Compose
- Python 3.8+
- PostgreSQL (or SQLite for local development)


### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/airplane-service.git
   cd airplane-service
   
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   cp .env.sample .env
   ```
   Fill in the `.env` file with necessary configurations.

5. Run database migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```
   
## Running the API
### Using Docker
#### To run the API using Docker, follow these steps:

- Ensure Docker and Docker Compose are installed.
- You can pull doker using command:
  ```bash
   docker pull kkkkkkkktya/airport_service
   ```
- Build and start the containers:
  ```bash
   docker-compose up --build
   ```

  The API will be accessible at http://localhost:8000/ once the containers are up and running.
### Using localhost
  If you prefer to run the API locally without Docker, follow these steps:

Start the development server:
  ```bash
    python manage.py runserver
  ```
Access the API at http://127.0.0.1:8000/.

## Authentication
The API uses JWT (JSON Web Tokens) for authentication. To obtain a token:

1. **Register a user** (see the Registration endpoint in the API documentation).
2. **Login** with the registered credentials to receive a token.
3. Include the token in the Authorization header for subsequent requests:


## Usage
- Visit `http://127.0.0.1:8000/` in your browser.
- Register and get your token to create an orders.
- View all airport service info and create some yourself.

## Support
For support, open an issue on [GitHub Issues](https://github.com/your-username/task-manager/issues) or contact the maintainers.

## Roadmap
- Implement notifications for flight
- Add front-end for api

## Contributing
Contributions are welcome! Follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them.
4. Push the changes to your fork and create a pull request.

## Authors and Acknowledgment
Developed by Kateryna

## Project Status
Active - ongoing development and improvements.
 
