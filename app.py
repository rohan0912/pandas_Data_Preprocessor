from flask import Flask, render_template, request, redirect, url_for, send_file, session
from flask_session import Session  # You might need to install Flask-Session
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
import os

app = Flask(__name__)
# Configure Flask Session
app.config["SECRET_KEY"] = "your_very_secret_key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            # Load the dataframe and store it in the session
            df = pd.read_csv(filename)
            session['df'] = df.to_json(date_format='iso', orient='split')
            return redirect(url_for('process_csv', filename=file.filename))
    return render_template('upload.html')


@app.route('/process_csv/<filename>', methods=['GET', 'POST'])
def process_csv(filename):
    processed = False
    action = request.form.get('action')

    # Load the dataframe from the session
    if 'df' in session:
        df = pd.read_json(session['df'], orient='split')
    else:
        return redirect(url_for('upload_file'))

    # Compute dataset statistics
    num_columns = len(df.columns)
    num_rows = len(df)
    num_duplicates = len(df) - len(df.drop_duplicates())

    # Calculate missing values information
    missing_values = df.isnull().sum()
    total_missing_values = missing_values.sum()
    columns_missing_values = missing_values.reset_index()
    columns_missing_values.columns = ['Column', 'Missing Values']

    columns_list = df.columns.tolist()


    if action == 'remove_missing':
        if total_missing_values == 0:
            error_message = f"No missing value in the dataset"
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message,num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)
        else:
            df.dropna(inplace=True)
        processed = True

    elif action == 'rename_column':
        old_column_name = request.form.get('old_column_name')
        new_column_name = request.form.get('new_column_name')
        if old_column_name in df.columns:
            df.rename(columns={old_column_name: new_column_name}, inplace=True)
            processed = True
        else:
            error_message = f"Error: Column '{old_column_name}' does not exist."
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message,num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

    elif action == 'remove_duplicates':
        df.drop_duplicates(inplace=True)
        processed = True

    elif action == "drop_column":
        column_drop = request.form.get('column_drop')
        if column_drop in df.columns:
            df = df.drop(column_drop, axis=1)
            processed = True
        else:
            error_message = f"Error: Column '{old_column_name}' does not exist."
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message,num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)


    elif action == 'convert_datatype':
        column_name = request.form.get('column_name')
        target_datatype = request.form.get('target_datatype')
        if column_name in df.columns:
            try:
                df[column_name] = df[column_name].astype(target_datatype)
                processed = True
            except ValueError as e:
                return render_template('process_csv.html', filename=filename, processed=False, error_message=str(e), num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

    elif action == 'replace_missing_with':
        column_name = request.form.get('column_name')
        replacement_method = request.form.get('replacement_method')

        if column_name not in df.columns:
            error_message = f"Error: Column '{column_name}' does not exist."
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

        if replacement_method in ['mean', 'median'] and not pd.api.types.is_numeric_dtype(df[column_name]):
            error_message = "Error: Mean and median can only be applied to numeric columns."
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

        if replacement_method == 'mean':
            df[column_name].fillna(df[column_name].mean(), inplace=True)
        elif replacement_method == 'median':
            df[column_name].fillna(df[column_name].median(), inplace=True)
        elif replacement_method == 'mode':
            df[column_name].fillna(df[column_name].mode()[0],inplace=True)  # mode() returns a Series, use [0] to get value
        processed = True


    elif action == 'convert_datetime_format':
        column_name = request.form.get('datetime_column_name')
        datetime_format = request.form.get('datetime_format')

        if column_name not in df.columns:
            error_message = f"Error: Column '{column_name}' does not exist."
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

        try:
            if datetime_format == 'unix':
                # Convert Unix timestamp to datetime
                df[column_name] = pd.to_datetime(df[column_name], unit='ms')
            else:
                # Convert column to specified datetime format
                df[column_name] = pd.to_datetime(df[column_name]).dt.strftime(datetime_format)
            processed = True
        except ValueError as e:
            error_message = f"Error converting datetime format: {str(e)}"
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

    elif action == "norm":
        column_name_norm = request.form.get('column_name_norm')

        if column_name_norm not in df.columns:
            error_message = f"Error: Column '{column_name_norm}' does not exist."
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

        if not pd.api.types.is_numeric_dtype(df[column_name_norm]):
            error_message = "Error: Can only be applied to numeric columns."
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

        scaler = MinMaxScaler(feature_range=(0, 1))
        df['Scores_normalized'] = scaler.fit_transform(df[[column_name_norm]])
        processed = True


    elif action == "stand":
        column_name_stand = request.form.get('column_name_stand')

        if column_name_stand not in df.columns:
            error_message = f"Error: Column '{column_name_stand}' does not exist."
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

        if not pd.api.types.is_numeric_dtype(df[column_name_stand]):
            error_message = "Error: Can only be applied to numeric columns."
            return render_template('process_csv.html', filename=filename, processed=False, error_message=error_message, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list=columns_list)

        scaler = StandardScaler()
        df['Scores_Standardized'] = scaler.fit_transform(df[[column_name_stand]])
        processed = True



    # After operation, update dataframe in session
    if processed:
        session['df'] = df.to_json(date_format='iso', orient='split')
        cleaned_filename = f"cleaned_{filename}"
        cleaned_file_path = os.path.join(app.config['UPLOAD_FOLDER'], cleaned_filename)
        df.to_csv(cleaned_file_path, index=False)

        num_columns = len(df.columns)
        num_rows = len(df)
        num_duplicates = len(df) - len(df.drop_duplicates())

        # Calculate missing values information
        missing_values = df.isnull().sum()
        total_missing_values = missing_values.sum()
        columns_missing_values = missing_values.reset_index()
        columns_missing_values.columns = ['Column', 'Missing Values']
        columns_list = df.columns.tolist()
        # Proceed with returning your template and context
        return render_template('process_csv.html', filename=filename, processed=processed,
                               cleaned_filename=cleaned_filename, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list = columns_list)

    # If no operation is processed, just show the options again
    return render_template('process_csv.html', filename=filename, processed=processed, num_columns=num_columns, num_rows=num_rows, num_duplicates=num_duplicates,
                           columns_missing_values=columns_missing_values.to_dict('records'),
                           total_missing_values=total_missing_values, columns_list = columns_list)


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)