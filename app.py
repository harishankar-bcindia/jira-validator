import streamlit as st
import pandas as pd
from jira_API import jira_data
from main_API import call_crew_api
from main import call_crew
import csv
import base64
from main import output_df_list
from main_API import output_df_list_api
from threading import Thread
import time


#create a task of 10 threads
#start that task
#wait for the responses of that task



if "uploader" not in st.session_state :
    st.session_state.uploader = False

if "jira_api" not in st.session_state :
    st.session_state.jira_api = False

if "buttons" not in st.session_state :
    st.session_state.buttons = False

if "default" not in st.session_state :
    st.session_state.default = True

if "crew" not in st.session_state :
    st.session_state.crew = False

if "table" not in st.session_state :
    st.session_state.table = None

if "output1" not in st.session_state :
    st.session_state.output1 = None

if "output1_new" not in st.session_state :
    st.session_state.output1_new = None

def excel_download1(df):
    csv_string1 = df.to_csv(index=False)
    csv_bytes1 = csv_string1.encode()
    return csv_bytes1

def excel_download(df):
    # csv_string1 = df.to_csv(index=False)
    # csv_bytes1 = csv_string1.encode()


    csv_file = df.to_csv(index=False)
    b64 = base64.b64encode(csv_file.encode()).decode()  # Encodes the CSV file as base64
    href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">Download Validator''s Output</a>'  # Creates download link

    return href


def create_matrix(row):
    matrix_data = [
        ["Description",row['Description Original'], row['New Description'], row['Description Comment']],
        ["Story Points",row['Story Points Original'], row['Expected Story Points'], row['Story Points Comment']],
        ["Ticket Type",row['Ticket Type Original'], row['Ticket Type'], row['Ticket Comment']]
        # Add more rows as needed
    ]
    return pd.DataFrame(matrix_data, columns=['Key Attributes','Original', 'Generated', 'Comment'])

def main():
    logo = "image.webp"  # Adjust path to your logo image

    st.sidebar.markdown(
        """
        <style>
        [data-testid="stImage"] img {
            border-radius: 50%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.image(logo)
        st.title("Jira Validator")
        st.subheader("Using Sheet Uploader")
        uploader_button = st.button("Open File Uploader Interface")
        st.subheader("Using Jira API")
        api_button = st.button("Open Jira API Interface")
        if uploader_button:
            st.session_state.uploader = True
            st.session_state.jira_api = False
            st.session_state.default = False
        if api_button:
            st.session_state.jira_api = True
            st.session_state.uploader = False
            st.session_state.default = False

    if st.session_state.uploader:
        st.title("Using CSV Uploader")
        uploaded_file = st.file_uploader("Upload a file", type=['csv','xlsx'])
        # Checkbox with 4 options
        st.title("Agents")
        option1 = st.checkbox("Validator Agent")
        option2 = st.checkbox("Generator Agent")
        crew_button = st.button("Execute Crew")
        # option3 = st.checkbox("Story Points Validator")
        # option4 = st.checkbox("Ticket Type Classifier")
        # option5 = st.checkbox("Label Validator")
        # option6 = st.checkbox("Component Validator")
        # option7 = st.checkbox("Epic Linkage Validator")

        # Submit button
        if crew_button:
                if uploaded_file is not None:
                    try:
                        file_extension = uploaded_file.name.split(".")[-1]

                        if file_extension.lower() == "csv":
                            # Read CSV file
                            df = pd.read_csv(uploaded_file)
                        else:
                            # Read Excel file
                            df = pd.read_excel(uploaded_file)

                        with st.spinner('Loading...'):
                                df=df.replace('#','',regex=True)
                                df_new_2 = df.head(1)
                                mini_df_list = []
                                #creates chunks_df of the whole df and store it in the list.
                                chunk_size = 10
                                for i in range(0, len(df_new_2), chunk_size):
                                    subset = df_new_2.iloc[i:i+chunk_size]
                                    mini_df_list.append(subset)

                                #iterate each chunk df from mini_df_list
                                for sub_df in mini_df_list:
                                    threads_list = []
                                # Creating and storing threads for each row of chunk df in thread_list
                                    for index, row in sub_df.iterrows():
                                        single_row_df = pd.DataFrame([row])
                                        threads_list.append(Thread(target=call_crew, args=(single_row_df,)))
                                 #executing each thread of chunk df
                                    for thread in threads_list:
                                        thread.start()
                                    for thread in threads_list:
                                        thread.join()
                                #storing each of the output from each chunk in a temp df - output_df_list, and finally converting it into dict and downloading it.
                                output = pd.DataFrame.from_records(output_df_list)


                                # output = call_crew(dataframe = df.head(2),agents_list = [])
                                st.session_state.output1 = output
                                view = output.style.hide(axis="index")
                                view.set_table_styles([
                                            {'selector': "th", 'props': [("font-weight", "bold"), ("text-transform", "capitalize")]},{'selector': "td", 'props': [("font-size", "15px"),("vertical-align","top"),('text-align', 'left'), ("text-transform", "capitalize")]}
                                        ])

                                columns_to_drop = [0, 1,7,11,12,13,16,17,18,19,20]

                                df_new = output.drop(output.columns[columns_to_drop], axis=1)

                                st.session_state.output1_new = df_new
                                print("df_new",df_new)
                                st.markdown(excel_download(st.session_state.output1_new), unsafe_allow_html=True)

                                for index,row in output.iterrows():
                                    row_data = create_matrix(row)
                                    st.subheader(row['Summary Original'])
                                    view = row_data.style.hide(axis="index")

                                    view.set_table_styles([
                                            {'selector': "th", 'props': [("font-weight", "bold"), ("text-transform", "capitalize")]},{'selector': "td", 'props': [("font-size", "15px"),("vertical-align","top"),('text-align', 'left'), ("text-transform", "capitalize")]}
                                        ])
                                    # st.table(row_data)
                                    st.session_state.table = view
                                    st.markdown(st.session_state.table.to_html(),unsafe_allow_html=True)
                                st.download_button("Download CSV",excel_download1(st.session_state.output1),"Jira Output.csv",'text/csv')

                    except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please upload a file.")


    if st.session_state.jira_api:
        st.title("Using Jira API")
        project_name = st.text_input("Enter your Project Name")
        if project_name:

                if st.button("Execute Crew"):
                    with st.spinner('Loading...'):
                        jira_dataframe = jira_data(project_name)
                        print("DATAFRAME Shape is: ",jira_dataframe.shape)
                        # print("JIRA API data is ABove")

                        df_new_api = jira_dataframe.head(5)
                        mini_df_list = []
                        chunk_size = 5
                        for i in range(0, len(df_new_api), chunk_size):
                            subset = df_new_api.iloc[i:i+chunk_size]
                            mini_df_list.append(subset)

                        for sub_df in mini_df_list:
                            threads_list = []
                            for index, row in sub_df.iterrows():
                                single_row_df = pd.DataFrame([row])


                                thread_1 = Thread(target=call_crew_api, args=(single_row_df,))
                                threads_list.append(thread_1)
                            for thread in threads_list:
                                thread.start()
                            for thread in threads_list:
                                thread.join()

                        output1 = pd.DataFrame.from_records(output_df_list_api)
                        # print("Harishanakr")
                        # print(output1)



                        # output1 = call_crew_api(dataframe = jira_dataframe.head(1),agents_list = [])
                        view = output1.style.hide(axis="index")
                        view.set_table_styles([
                                    {'selector': "th", 'props': [("font-weight", "bold"), ("text-transform", "capitalize")]},{'selector': "td", 'props': [("font-size", "15px"),("vertical-align","top"),('text-align', 'left'), ("text-transform", "capitalize")]}
                                ])

                        columns_to_drop = [0, 1,7,11,12,13,16,17,18,19,20]
                        df_new = output1.drop(output1.columns[columns_to_drop], axis=1)
                        st.session_state.output1_new = df_new
                        st.markdown(excel_download(st.session_state.output1_new), unsafe_allow_html=True)

                        for index,row in output1.iterrows():
                            row_data = create_matrix(row)
                            st.subheader(row['Summary Original'])
                            view1 = row_data.style.hide(axis="index")

                            view1.set_table_styles([
                                    {'selector': "th", 'props': [("font-weight", "bold"), ("text-transform", "capitalize")]},{'selector': "td", 'props': [("font-size", "15px"),("vertical-align","top"),('text-align', 'left'), ("text-transform", "capitalize")]}
                                ])
                            # st.table(row_data)
                            st.markdown(view1.to_html(),unsafe_allow_html=True)
                        st.download_button("Download CSV",excel_download1(output1),"Jira Output.csv",'text/csv')



    if st.session_state.default:
        st.title("Welcome to JIRA Validator")
        st.subheader("This is a web application to validate the Jira tickets.")

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    with open("style.css") as source_des:
        st.markdown(f"<style>{source_des.read()}</style>", unsafe_allow_html=True)
    main()
