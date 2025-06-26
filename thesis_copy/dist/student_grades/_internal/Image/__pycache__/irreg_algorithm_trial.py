import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering

def process_data(old_file_path, new_file_path):
    def map_year_semester(year_semester):
        try:
            year_semester = str(year_semester)
            if '.' in year_semester:
                year, semester = year_semester.split('.')
                return f"Y{year}S{semester}"
            else:
                return np.nan
        except ValueError:
            return np.nan

    # Load the datasets for old and new curricula
    df_old = pd.read_csv(old_file_path)
    df_new = pd.read_csv(new_file_path)

    # Ensure 'Course No.' and 'Prerequisite' remain as strings
    df_old['Course No.'] = df_old['Course No.'].astype(str).str.strip()
    df_new['Course No.'] = df_new['Course No.'].astype(str).str.strip()
    df_old['Prerequisite'] = df_old['Prerequisite'].astype(str).str.strip()
    df_new['Prerequisite'] = df_new['Prerequisite'].astype(str).str.strip()

    # Check for uniqueness in 'Course No.' column only
    if not df_old['Course No.'].is_unique:
        raise ValueError("Old curriculum 'Course No.' contains duplicate values.")
    if not df_new['Course No.'].is_unique:
        raise ValueError("New curriculum 'Course No.' contains duplicate values.")

    # Replace 'N/A' values with NaN and convert numerical columns
    for df in [df_old, df_new]:
        df['Units'] = df['Units'].replace('N/A', np.nan)
        df['Lab'] = df['Lab'].replace('N/A', np.nan)
        df['Lec'] = df['Lec'].replace('N/A', np.nan)
        df['Units'] = pd.to_numeric(df['Units'], errors='coerce')
        df['Lab'] = pd.to_numeric(df['Lab'], errors='coerce')
        df['Lec'] = pd.to_numeric(df['Lec'], errors='coerce')
        df['Year Level'] = df['Year Level'].astype(str)
        df['Year Level Code'] = df['Year Level'].apply(map_year_semester)

    # Filter the old curriculum to show only subjects that have grades
    subjects_with_grades_old = df_old[df_old['Grades'].notna()]

    # Match the filtered old curriculum subjects with the new curriculum
    matched_subjects = pd.merge(subjects_with_grades_old[['Course No.', 'Descriptive Title', 'Grades']],
                                 df_new, on='Course No.', how='left')

    # Drop rows where the 'Course No.' from the old curriculum is not found in the new curriculum
    matched_subjects = matched_subjects.dropna(subset=['Descriptive Title_y'])

    # Get the list of matched Course Nos. from the new curriculum
    matched_course_nos = matched_subjects['Course No.'].unique()

    # Filter the old curriculum based on matched subjects
    filtered_old = subjects_with_grades_old[subjects_with_grades_old['Course No.'].isin(matched_course_nos)]

    # Now proceed with the clustering on the new curriculum
    df_new_filtered = df_new[df_new['Course No.'].isin(matched_course_nos)]

    year_semester_mapping = {
        "Y1S1": 1, "Y1S2": 2,
        "Y2S1": 3, "Y2S2": 4,
        "Y3S1": 5, "Y3S2": 6,
        "Y4S1": 7, "Y4S2": 8
    }
    df_new_filtered['Year Level Num'] = df_new_filtered['Year Level Code'].map(year_semester_mapping)
    df_new_filtered = df_new_filtered.dropna(subset=['Year Level Num'])

    clustered_data = pd.DataFrame()
    year_levels = df_new_filtered['Year Level Num'].unique()

    for year_level in year_levels:
        year_level_df = df_new_filtered[df_new_filtered['Year Level Num'] == year_level]

        # Extract features for clustering
        features = year_level_df[['Units', 'Lab', 'Lec']].values

        # Check if there are enough samples to cluster
        if len(features) < 2:  # Need at least 2 samples for clustering
            continue

        # Standardize the features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        # Apply hierarchical clustering
        clustering = AgglomerativeClustering(n_clusters=2, linkage='ward')  # Adjust n_clusters as needed
        cluster_labels = clustering.fit_predict(scaled_features)

        # Add cluster labels to the DataFrame
        year_level_df['Cluster'] = cluster_labels

        # Append to the final clustered data
        clustered_data = pd.concat([clustered_data, year_level_df], ignore_index=True)

    # Include the Grade column from matched subjects
    clustered_data = pd.merge(clustered_data, matched_subjects[['Course No.', 'Grades']], on='Course No.', how='left')

    # Calculate total Units, Lab, and Lec for each cluster in each semester
    total_summary = clustered_data.groupby(['Year Level Code', 'Cluster']).agg(
        Total_Units=('Units', 'sum'),
        Total_Lab=('Lab', 'sum'),
        Total_Lec=('Lec', 'sum')
    ).reset_index()

    # Sort the clustered data by semester and year level
    clustered_data['Semester'] = clustered_data['Year Level Code'].apply(lambda x: x.split('S')[1] if isinstance(x, str) else np.nan)
    clustered_data = clustered_data.sort_values(by=['Year Level Num', 'Semester'])

    # Prepare the final output with clusters and subjects
    final_output = []

    for year_level_code in clustered_data['Year Level Code'].unique():
        year_level_data = clustered_data[clustered_data['Year Level Code'] == year_level_code]
        for cluster in year_level_data['Cluster'].unique():
            cluster_data = year_level_data[year_level_data['Cluster'] == cluster]
            total_row = total_summary[(total_summary['Year Level Code'] == year_level_code) & (total_summary['Cluster'] == cluster)].copy()
            total_row['Course No.'] = 'Total'
            total_row['Descriptive Title'] = ''
            total_row['Grades'] = ''
            final_output.append(cluster_data)
            final_output.append(total_row)

    final_output_df = pd.concat(final_output, ignore_index=True)

    # Remove the 'Total_Units', 'Total_Lab', 'Total_Lec', and 'Cluster' columns
    final_output_df = final_output_df.drop(columns=['Total_Units', 'Total_Lab', 'Total_Lec', 'Cluster'])

    return matched_subjects, final_output_df

# File paths
old_file_path = 'C:/Users/Acer/OneDrive/Documents/Thesis_Estorque/Data_Curri/OldCurri_Sample.csv'
new_file_path = 'C:/Users/Acer/OneDrive/Documents/Thesis_Estorque/Data_Curri/curri.csv'

# Process the data
matched_subjects, final_output = process_data(old_file_path, new_file_path)

# Output results
print("Matched Subjects with Grades:")
print(matched_subjects)

# Set pandas display options to show all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

print("\nClustered Data with Subjects and Totals Below Each Cluster:")
print(final_output)
