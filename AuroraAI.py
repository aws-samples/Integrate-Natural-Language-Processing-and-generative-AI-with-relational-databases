from flask import Flask, render_template, request, jsonify, send_file
import boto3
import base64
import json
import os
import base64
import psycopg2
import re

# dc - 2024-12-04 - Initialize Flask application
app = Flask(__name__)

# dc - 2024-12-04 - Ensure templates directory exists for Flask views
os.makedirs('templates', exist_ok=True)

# dc - 2024-12-04 - Create index.html template with HTML/CSS/JavaScript content
with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Report Generator</title>
    <!-- dc - 2024-12-04 - Include Bootstrap CSS for styling -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        /* dc - 2024-12-04 - Base styling for body content */
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        /* dc - 2024-12-04 - Container styling for prompt input area */
        .prompt-container {
            width: 100%;
            margin: 20px 0;
        }
        /* dc - 2024-12-04 - Styling for the textarea input field */
        .prompt-input {
            width: 80%;
            height: 150px;
            padding: 12px 20px;
            margin: 8px 0;
            box-sizing: border-box;
            border: 2px solid #ccc;
            border-radius: 4px;
            background-color: #f8f8f8;
            font-size: 16px;
            resize: vertical;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        .warning-box {
            background-color: #ffff99;
            color: #003300;
            border: 1px solid #ff0000;
            padding: 10px;
            margin: 10px auto;
            border-radius: 4px;
            font-size: 14px;
            display: block;           /* Makes the box fit to content width */
            width: 80%;              /* Allows box to size to content */
            min-width: min-content;   /* Ensures minimum width fits content */
            max-width: 100%;          /* Prevents overflow on small screens */
            box-sizing: border-box;   /* Includes padding in width calculation */
            white-space: normal;      /* Allows text to wrap naturally */
            line-height: 1.4;         /* Improves readability of wrapped text */
            text-align: center;       /* Centers the text inside */            
        }
        /* dc - 2024-12-04 - Styling for the submit button */
        .submit-btn {
            background-color: #4CAF50;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            display: block;
            margin: 20px auto;
            font-size: 16px;
        }
        /* dc - 2024-12-04 - Hover effect for submit button */
        .submit-btn:hover {
            background-color: #45a049;
        }
        /* dc - 2024-12-04 - Container styling for results table */
        .table-container {
            margin-top: 20px;
            overflow-x: auto;
        }
        /* dc - 2024-12-04 - Base table styling */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        /* dc - 2024-12-04 - Table cell styling */
        th, td {
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }
        /* dc - 2024-12-04 - Header row styling */
        th {
            background-color: #f2f2f2;
        }
        /* dc - 2024-12-04 - Alternating row colors */
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        /* dc - 2024-12-04 - Row hover effect */
        tr:hover {
            background-color: #f5f5f5;
        }
        /* dc - 2024-12-04 - Loading indicator styling */
        #loading {
            display: none;
            margin: 20px 0;
            font-style: italic;
            color: #666;
            text-align: center;
        }
        /* dc - 2024-12-04 - Page title styling */
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    <!-- dc - 2024-12-04 - Main page heading -->
    <h1>Report Generator</h1>
    <!-- dc - 2024-12-04 - Form container for user input -->
    <div class="prompt-container">
        <form id="promptForm">
            <textarea 
                class="prompt-input" 
                id="prompt" 
                placeholder="Enter the data to be retrieved from the database in plain text format"
                required></textarea>
            <div class="warning-box">
                Do not use the words 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER'
            </div>
            <button type="submit" class="submit-btn">Generate Report</button>
        </form>
    </div>

    <!-- dc - 2024-12-04 - Loading indicator element -->
    <div id="loading">Retrieving data, please wait...</div>
    
    <!-- dc - 2024-12-04 - Container for query results -->
    <div class="table-container" id="resultContainer"></div>

    <script>
        // dc - 2024-12-04 - Event listener for form submission
        document.getElementById('promptForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const prompt = document.getElementById('prompt').value;
            const loading = document.getElementById('loading');
            const resultContainer = document.getElementById('resultContainer');
            
            // dc - 2024-12-04 - Show loading state and clear previous results
            loading.style.display = 'block';
            resultContainer.innerHTML = '';

            try {
                // dc - 2024-12-04 - Send request to backend API
                console.log('Sending request to /generate');
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt: prompt })
                });
                
                console.log('Response received:', response);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('Data received:', data);
                    
                    // dc - 2024-12-04 - Generate dynamic table from response data
                    if (data.columns && data.rows) {
                        const table = document.createElement('table');
                        table.className = 'table table-striped table-bordered';
                        
                        // dc - 2024-12-04 - Create table header
                        const thead = document.createElement('thead');
                        const headerRow = document.createElement('tr');
                        data.columns.forEach(column => {
                            const th = document.createElement('th');
                            th.textContent = column;
                            headerRow.appendChild(th);
                        });
                        thead.appendChild(headerRow);
                        table.appendChild(thead);
                        
                        // dc - 2024-12-04 - Create table body with data
                        const tbody = document.createElement('tbody');
                        data.rows.forEach(row => {
                            const tr = document.createElement('tr');
                            row.forEach(cell => {
                                const td = document.createElement('td');
                                td.textContent = cell === null ? 'NULL' : cell;
                                tr.appendChild(td);
                            });
                            tbody.appendChild(tr);
                        });
                        table.appendChild(tbody);
                        
                        resultContainer.appendChild(table);
                    } else {
                        resultContainer.innerHTML = 'No data returned';
                    }
                } else {
                    // dc - 2024-12-04 - Handle error responses
                    const errorData = await response.json();
                    console.error('Server error:', errorData);
                    resultContainer.innerHTML = `Error: ${errorData.error || 'Unknown error'}`;
                }
            } catch (error) {
                // dc - 2024-12-04 - Handle network or other errors
                console.error('Error:', error);
                resultContainer.innerHTML = 'Error fetching results';
            } finally {
                // dc - 2024-12-04 - Hide loading indicator
                loading.style.display = 'none';
            }
        });
    </script>
</body>
</html>
    ''')

# dc - 2024-12-04 - Function to process user input and generate SQL using Bedrock AI
def call_bedrock(input_prompt):
    # Check for sql injection
    prompt_check = sql_injection_guardrail(input_prompt, 'prompt from user')
    if  prompt_check == 'forbidden':
        columns = ['Error message']
        data = [(0, 'I cannot execute any statement that modifies the database.')]
        # dc - 2024-12-04 - Return the query results or error message to the caller                    
        return columns, data
    else:
        # dc - 2024-12-04 - Get the table structure from the database
        conn, metadata = get_metadata()

        # dc - 2024-12-04 - Initialize Bedrock client for AI processing
        client_bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        # dc - 2024-12-04 - Construct prompt for AI model with safety constraints
        prompt_text = """
        Act as a developer writing SQL code for an Aurora Postgres database.
        Important: Do not generate any SQL that modifies data in the database. Only generate SELECT statements.
        Never generate INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, or any other data modification statements.
        Reject requests that contain the words change, modify, revise, replace.
        The database schema name is dc_ai_test and contains the following tables:
        """ + metadata + """
        Convert the following text to SQL query and only return the SQL query without any explanation.
        """ + input_prompt 
        print(prompt_text)

        # dc - 2024-12-04 - Configure Bedrock API request parameters
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
                        }
                    ]
                }
            ],
            "temperature": 0.4,  # Controls randomness in response
            "top_p": 0.999,
            "top_k": 250
        }
        try:
            # dc - 2024-12-04 - Call Bedrock API and process response
            response = client_bedrock.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps(body)
            )
            # dc - 2024-12-04 - Parse and extract SQL from response
            response_body = json.loads(response.get('body').read())
            sql_from_bedrock = response_body['content'][0]['text']
            # dc - 2024-12-04 - Check if any forbidden SQL operations were found in the response
            prompt_check = sql_injection_guardrail(sql_from_bedrock, 'SQL from AI model')
            if  prompt_check == 'forbidden':
                columns = ['Error message']
                data = [(0, 'I cannot execute any statement that modifies the database.')]
            else:
                # dc - 2024-12-04 - Verify if the SQL is a SELECT statement and execute if valid
                if sql_from_bedrock.lower().startswith('select'):
                    # dc - 2024-12-04 - Execute the validated SELECT query and retrieve results
                    columns, data = execute_sql(conn, sql_from_bedrock)
                else:
                    # dc - 2024-12-04 - Return error message if query is not a SELECT statement
                    columns = ['Error message']
                    data = [(0, 'I can only execute SELECT statements.')]
                # dc - 2024-12-04 - Return the query results or error message to the caller                    
            return columns, data
        except Exception as e:
            print(f"Error calling Claude: {str(e)}")
            return None            



def sql_injection_guardrail(prompt, caller):
    # dc - 2024-12-04 - Security check for forbidden SQL operations
    forbidden_words = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER']
    upper_response = prompt.upper()
    found_words = []
    for word in forbidden_words:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, upper_response):
            found_words.append(word)
    if found_words:
        print('Prohibited words found in', caller)
        print(prompt)
        print(found_words)
        return('forbidden')
    else:
        print('No prohibited words found in', caller)        
        return('allowed')



def get_metadata():
    try:
        # dc - 2024-12-04 - Log the start of database metadata retrieval
        print('Executing SQL')
        
        # dc - 2024-12-04 - Get database connection credentials from secure storage
        credentials = get_db_credentials()
        
        # dc - 2024-12-04 - Establish connection to PostgreSQL database using credentials
        conn = psycopg2.connect(
            dbname=credentials['db_name'],
            user=credentials['db_user'],
            password=credentials['db_password'],
            host=credentials['db_host'],
            port=credentials['db_port']
        )
        print("Connection successful!")
        
        # dc - 2024-12-04 - Create database cursor for executing queries
        cur = conn.cursor()
        
        # dc - 2024-12-04 - SQL query to retrieve comprehensive schema metadata
        sql_metadata = """
            SELECT  Json_agg(Json_build_object('table_schema', table_schema, 'table_name', table_name, 'column_name', column_name, 
                                               'data_type', data_type, 'size', size, 'key_type', key_type))
            FROM   (
                        SELECT  
                                    t.table_schema,
                                    t.table_name,
                                    c.column_name,
                                    c.data_type,
                                    CASE
                                        WHEN c.character_maximum_length IS NOT NULL THEN c.character_maximum_length
                                        WHEN c.numeric_precision        IS NOT NULL THEN c.numeric_precision
                                        ELSE NULL
                                    END AS size,
                                    CASE
                                        WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'PK'
                                        WHEN tc.constraint_type = 'FOREIGN KEY' THEN 'FK'
                                        ELSE 'Not a key'
                                    END AS key_type
                        FROM        information_schema.tables t
                        JOIN        information_schema.columns c
                        ON        t.table_name = c.table_name
                        AND        t.table_schema = c.table_schema
                        LEFT JOIN   information_schema.key_column_usage kcu
                        ON        c.column_name = kcu.column_name
                        AND        c.table_name = kcu.table_name
                        AND        c.table_schema = kcu.table_schema
                        LEFT JOIN   information_schema.table_constraints tc
                        ON        kcu.constraint_name = tc.constraint_name
                        AND        kcu.table_name = tc.table_name
                        AND        kcu.table_schema = tc.table_schema
                        WHERE       t.table_schema = 'dc_ai_test'
                        AND       t.table_type = 'BASE TABLE'
                        ORDER BY    t.table_name,
                                    c.ordinal_position
                    ) subquery
                    ;
        """
        
        # dc - 2024-12-04 - Execute the metadata query
        cur.execute(sql_metadata)
        print('SQL executed successfully')            
        
        # dc - 2024-12-04 - Convert query results to JSON format
        metadata = json.dumps(cur.fetchall())
        
        # dc - 2024-12-04 - Close cursor to free up database resources
        cur.close()
        
        # dc - 2024-12-04 - Return both the database connection and metadata
        return conn, metadata
        
    except Exception as e:
        # dc - 2024-12-04 - Log and handle any database connection or query errors
        print(f"Error: {str(e)}")
        return None, None



def get_db_credentials():
    # dc - 2024-12-04 - Initialize AWS Secrets Manager client for us-east-1 region
    client = boto3.client('secretsmanager', region_name='us-east-1')
    
    try:
        # dc - 2024-12-04 - Retrieve secret value from AWS Secrets Manager using AuroraAI secret ID
        response = client.get_secret_value(SecretId='AuroraAI')
        
        # dc - 2024-12-04 - Parse the secret string into a Python dictionary
        secret_dict = json.loads(response['SecretString'])
        
        # dc - 2024-12-04 - Return formatted credentials dictionary for database connection
        return {
            'db_name': secret_dict['DB_NAME'],
            'db_user': secret_dict['DB_USER'],
            'db_password': secret_dict['DB_PASSWORD'],
            'db_host': secret_dict['DB_HOST'],
            'db_port': secret_dict['DB_PORT']
        }
    except Exception as e:
        # dc - 2024-12-04 - Log any errors in retrieving or processing credentials
        print(f"Error retrieving secret: {str(e)}")
        return None



def execute_sql(conn, sql_from_bedrock):
    try:
        # dc - 2024-12-04 - Log the start of SQL execution process
        print('Executing SQL')
        print(sql_from_bedrock)
               
        # dc - 2024-12-04 - Create cursor for executing the SQL query
        cur = conn.cursor()
        
        # dc - 2024-12-04 - Execute the AI-generated SQL query
        cur.execute(sql_from_bedrock)
        print('SQL executed successfully')            
        
        # dc - 2024-12-04 - Extract column names from the query results
        columns = [desc[0] for desc in cur.description]
        
        # dc - 2024-12-04 - Fetch all rows from the query results
        data = cur.fetchall()   
        
        # dc - 2024-12-04 - Clean up database resources
        cur.close()
        conn.close()
        print("Connection closed")
        
        # dc - 2024-12-04 - Return both column names and data rows
        return columns, data
            
    except Exception as e:
        # dc - 2024-12-04 - Log any errors and return empty result set
        print(f"Error: {str(e)}")
        return None, None



# dc - 2024-12-04 - Route handler for the main application homepage
@app.route('/')
def home():
    return render_template('index.html')

# dc - 2024-12-04 - API endpoint for handling natural language to SQL generation requests
@app.route('/generate', methods=['POST'])
def generate():
    try:
        # dc - 2024-12-04 - Extract JSON data from the incoming POST request
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        # dc - 2024-12-04 - Call Bedrock AI service to generate and execute SQL query
        columns, rows = call_bedrock(prompt)
        
        # dc - 2024-12-04 - Return query results if data is found
        if  columns and rows:
            return jsonify({
                'columns': columns,
                'rows': rows
            })
        else:
            # dc - 2024-12-04 - Return 404 error if no data is found
            return jsonify({'error': 'No data returned'}), 404
            
    except Exception as e:
        # dc - 2024-12-04 - Log and return any errors that occur during processing
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# dc - 2024-12-04 - Application entry point with security configurations
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

