import streamlit as st
import pandas as pd
# from crewAI.src.crewai import Crew, Agent, Task, Process
from crewai import Crew, Agent, Task, Process

import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from openpyxl import load_workbook,Workbook
from langchain.agents import initialize_agent, Tool
from openai import AzureOpenAI, AsyncOpenAI
from langchain_openai import ChatOpenAI
import datetime
from langchain_community.document_loaders import PyPDFLoader

import warnings

import logging
import ast

output_df_list_api = []


def handling_gpt_ouput(gpt_response):
    try:
        # Try parsing the variable as a list
        parsed_variable = ast.literal_eval(gpt_response)
        logging.info('GPT response parsed successfully.')
        if isinstance(parsed_variable, list):
            # If it's already a list, return it as is
            logging.info('GPT response is already a JSON inside list.')
            return parsed_variable
    except (ValueError, SyntaxError):
        pass

    # Extract content between first and last curly braces
    start_index = gpt_response.find('{')
    end_index = gpt_response.rfind('}')

    if start_index != -1 and end_index != -1:
        extracted_content = gpt_response[start_index:end_index + 1]
        logging.info(f'Extracted GPT response as JSON in string format: {extracted_content}')
        output = eval(extracted_content)
        logging.info(f'Evaluated(eval()) string JSON response inside list: {[output]}')
        return  [output]  # Return the extracted content as a list
    logging.exception(f'handling_gpt_output_failed()- returning empty list :{gpt_response}')
    return []  # Return an empty list if extraction fails
# a = handling_gpt_ouput(result)
# print(a[0]["output"][1])

def crew_agent(ticket_detail):    #ticket detail is the df of each row.
    llm = ChatOpenAI(model="gpt-4-1106-preview",api_key=os.getenv("OPENAI_API_KEY"))

    ticket_dict = ticket_detail.to_dict(orient="records")

    output_json = [
                    {
                        "is_summary_meaningful" : "Yes or No",
                        "is_summary_with_description_meaningful" : "Yes or No",
                        "is_summary_with_issuetype_meaningful" : "Yes or No",
                        "your_reason" : "Your reason, why you selected Yes or No"
                    },
                    {
                        "is_description_present" : "Yes or No",
                        "is_description_meaningful" : "Yes or No",
                        "has_acceptance_criteria" : "Yes or No",
                        "new_description": "Based on the summary, what should be ideal description that descibes the acceptance criteria if required.",
                        "your_reason" : "Your reason, why you selected Yes or No"
                    },
                    {
                        "is_story_points_present" : "Yes or No",
                        "is_story_points_meaningful" : "Yes or No",
                        "expected_story_points" : "",
                        "your_reason" : "Your reason, why you selected Yes or No",

                    },
                    {
                        "ticket_type" : "Bug or Issue or Feature",
                        "your_reason" : "Your reason, why you selected any one from Bug/Issue/Feature"

                    },
                    {
                        "is_label_present" : "Yes or No"
                    },
                    {
                        "is_component_present" : "Yes or No"
                    },
                    {
                        "is_epic_present" : "Yes or No"
                    }
                ]

    task_description = f''' You have to fill complete raw json format provided based on your analysis of JIRA ticket.
                Overall Raw Json to fill is: {output_json} \n\
                Ticket details are : {ticket_dict} .
                Analyse above ticket details, But before filling raw json you have to analyze below things carefully in ticket and do not write any comment in your output and return only filled raw json, do not delete or add any extra key:

                            Instruction 1: Analyze ticket summary and complete this part based on the conditions provided {output_json[0]},
                               If ticket summary is meaningful, short yet descriptive, if yes then fill Yes else No in this key ->is_summary_meaningful.
                                If ticket summary aligned with the description, whether the summary and description combined makes sense then is it meaningful, if yes then fill Yes else No in this key ->  is_summary_with_description_meaningful.
                                If ticket summary aligned with the issue type it belongs to, whether the summary is aligned with the type of issue it is, then is it meaningful, if yes then fill Yes else No in this key ->  is_summary_with_issuetype_meaningful.
                                And in key -> your_reason, provide the reason to select the above values.
                                And do not add any comment like //.

                            Instruction 2: Analyze ticket description and complete this part based on the conditions provided {output_json[1]},
                                If ticket has desciption or not then fill Yes or No in this key -> is_description_present.
                                If ticket has description then is it meaningful and totally describe the issue in a proper way which can be understood by any team members. The description should be that clear that anyone could understand what needs to be done. Is it if yes then fill Yes else No in this key ->  is_description_meaningful.
                                If ticket description contains the acceptance criteria, if yes then fill Yes else No in this key ->has_acceptance_criteria.
                                If ticket is not meaningful and does not have acceptance criteria, then based on the ticket summary generate a new description for that ticket and if acceptance criteria can be generated then generate it in Even,When and Then format. Only when the description is meaninful and has an acceptance criteria, only then the new description should not be generated. In key -> new_description
                                In key -> your_reason, provide the reason to select the above values.
                                And do not add any comment like //.

                            Instruction 3: Analyze ticket story points and complete this part based on the conditions provided {output_json[2]},
                                If ticket has story points values or not then fill Yes or No in this key -> is_story_points_present.
                                If ticket has story points then are these story points justifiable to the actual efforts required to properly complete the task based on summary,description and the issue type it belongs to given that 1 story is equivalent to 1 day of effort,
                                You should understand that the complexity is highest to lowest for the following issue types:
                                                            Epic: represents a large body of work that can be broken down into smaller tasks or stories
                                                            Story: Represents a user requirement or functionality that delivers value to the end-user.
                                                            Task: Represents a piece of work that needs to be completed but doesn't deliver direct value to the end-user.They are usually smaller in scope and effort compared to stories.
                                                            Bug: Represents an issue or problem in the software that needs to be fixed.
                                                            Sub-task: Represents a smaller piece of work that is part of a larger task or story.
                                You should analyse the ticket summary and description and the level of complexity and decide whether the assigned story points and justifiable or not. You should analyse critically and then return then expected story points.
                                if yes then fill Yes else No in this key ->  is_story_points_meaningful.
                                And in key -> expected_story_points, provide and calculate your expected story points based on the title,description and the type of issue it belongs to, to be required to complete the task if the resource allocated to complete that task is a mid-level resource. The expected story points should be in number i.e 1,2 etc. Make sure you don't miss providing expected story points. And it should be justifiable. If summary and description are present and meaningful then use that to estimate the compexity and the calculate the estimated story points. If not then use the new description generated above as the basis to understand the complexity that ticket must have based on the issue type it belongs to and then estimate the expected story points.
                                Make sure the expected story points are assigned only in numbers. Critically examine and estimate the story points.
                                1 story points is equivalent to 8 hours of human effort, if some task just needs few hours, the expected story points should be in multiples of 0.25 of 1 story points. Never miss to assign story points.
                                And in key -> your_reason, provide the reason to select above values.
                                And do not add any comment like //.

                            Instruction 4: Analyze overall ticket, mainly the title and the decription, and complete this part based on the conditions provided {output_json[3]},
                                According to your overall analysis what should be the category of ticket: Bug or Feature or Other. You should refer to the below definition:
                                Bug: A flaw or defect in the software that causes it to behave unexpectedly or not as intended.
                                Feature: A new functionality or capability added to the software to enhance its usability or meet user requirements.
                                Other: Neither a bug nor a feature.
                                Always categorize into anyone of the categories: Bug, Feature or Others
                                Do not categorize into any other category other than Bug,Feature or Others. If something is not a Bug or a Feature then it is Others.
                                and fill any one in this key -> ticket_type
                                And in key -> your_reason, provide the reason to select above value.
                                And do not add any comment like //.

                            Instruction 5: Analyze ticket labels and complete this part based on conditions provided {output_json[4]},
                                If ticket has labels present or not then fill Yes or No in this key -> is_label_present.
                                And do not add any comment like //.

                            Instruction 6: Analyze ticket component and complete this part based on conditions provided {output_json[5]},
                                If ticket has components present or not then fill Yes or No in this key -> is_component_present.
                                And do not add any comment like //.

                            Instruction 7: Analyze ticket Epic Link Summary and complete this part based on the conditions provided{output_json[6]},
                                If Epic link summary is present then mark Yes, if it is not present then mark No in this key -> is_epic_present".
                                And do not add any comment like //.

                            Instruction 8: After overall analysis and filling of values to the corresponding keys now return complete filled json but do not delete any key of json even if it is empty.Do not Mention anything with HTML Tags markdown. And do not add any comment like //.


                '''
    # expected_output = f"Output should be only in this format after filling all appropriate details {output_json}"
    expected_output = 'Return only filled raw JSON as output key like this-> {"output" : filled_json}'

    Title_validator = Agent(
                            role = "Jira Ticket Validator",
                            goal = f"Analyze the JIRA ticket summary and description provided in the dictionary format and fill raw JSON" ,
                            backstory = f"You are the Scrum master whose task is to analyze the summary and description provided in the dictionary format. And after analysing the complete ticket, you have to fill complete raw json format provided.",
                            verbose = True,
                            allow_delegation = False,
                            llm = llm
                            )
    task_a = Task(
                    description=f"{task_description}",
                    expected_output=expected_output,
                    agent=Title_validator,

                    )
    crew = Crew(
        agents=[Title_validator],
        tasks=[task_a],
        verbose=1,
        )

    result = crew.kickoff()
    print({"crew_output ":result})
    output = handling_gpt_ouput(result)
    print({"handled_gpt_output":output})
    return output[0]["output"]


def generate_url(ticket_id):
    print(ticket_id)
    base_url = 'https://blenheimchalcot.atlassian.net/browse/'
    return base_url+str(ticket_id)

def append_row(dataframe,values,ticket_id,ticket_summary,ticket_description,ticket_story_points,ticket_type,labels,components,epic_link):
    values_dict = values
    print(ticket_description)
    data_to_append = {
                        'Ticket Id': str(ticket_id),
                        'Summary Original': str(ticket_summary),
                        'Summary Meaningful': str(values[0]["is_summary_meaningful"]),
                        'Summary & Description Aligned': str(values[0]["is_summary_with_description_meaningful"]),
                        'Summary & Issue Type Aligned': str(values[0]["is_summary_with_issuetype_meaningful"]),
                        'Summary Comment': str(values[0]["your_reason"]),
                        'Description Original': str(ticket_description),
                        'Description Present': str(values[1]["is_description_present"]),
                        'Description Meaningful': str(values[1]["is_description_meaningful"]),
                        'Description-Acceptance criteria': str(values[1]["has_acceptance_criteria"]),
                        'New Description':str(values[1]["new_description"]),
                        'Description Comment': str(values[1]["your_reason"]),
                        'Story Points Original': str(ticket_story_points),
                        'Story Points Present': str(values[2]["is_story_points_present"]),
                        'Story Points Meaningful': str(values[2]["is_story_points_meaningful"]),
                        'Expected Story Points': str(values[2]["expected_story_points"]),
                        'Story Points Comment': str(values[2]["your_reason"]),
                        'Ticket Type Original':str(ticket_type),
                        'Ticket Type': str(values[3]["ticket_type"]),
                        'Ticket Comment': str(values[3]["your_reason"]),
                        'Labels':str(labels),
                        'Labels Present': str(values[4]["is_label_present"]),
                        'Components': str(components),
                        'Components Present' : str(values[5]["is_component_present"]),
                        'Epic Summary' : str(epic_link),
                        'Epic Summary Present': str(values[6]["is_epic_present"])

                    }

    df = dataframe._append(data_to_append, ignore_index=True)
    print(df)
    return df

def extract_url(html_str):
    match = re.search(r'href="([^"]+)"', html_str)
    if match:
        return match.group(1)
    else:
        return None

def call_crew_api(df):


    # df = kwargs["dataframe"]
    # agents_dict = kwargs["agents_list"]
    tasks_list = []
    column_names =  ['Ticket Id','Summary Original', 'Summary Meaningful','Summary & Description Aligned','Summary & Issue Type Aligned','Summary Comment', 'Description Original','Description Present', 'Description Meaningful','Description-Acceptance criteria','New Description','Description Comment','Story Points Original', 'Story Points Present', 'Story Points Meaningful','Expected Story Points','Story Points Comment','Ticket Type Original','Ticket Type', 'Ticket Comment','Labels','Labels Present','Components','Components Present','Epic Summary','Epic Summary Present']
    output_df = pd.DataFrame(columns=column_names)
    # for key,value in agents_dict.items():
    #     if value:
    #         if key == "summary":
    #             tasks_list.append(key)
    #         elif key == "description":
    #             tasks_list.append(key)
    #         elif key == "story_points":
    #             tasks_list.append(key)
    #         elif key == "ticket_type":
    #             tasks_list.append(key)
    #         elif key == "labels":
    #             tasks_list.append(key)
    #         elif key == "components":
    #             tasks_list.append(key)
    #         elif key == "":
    #             task_loist.append(key)

    for index, row in df.iterrows():
        try:
            row_df = pd.DataFrame([row]) #creating a dataframe of single row so that each row can be given as input to GPT for futher processing.
            mini_df = row_df[["Summary","Description","Custom field (Story Points)","Labels","Components","Epic Link Summary"]]  #only those columns which are important.
            ticket_id = row_df["Issue key"][index]    #taking values of each columns as it is to store it later in the output for each row one by one.
            ticket_summary = row_df["Summary"][index]
            ticket_description = row_df["Description"][index]
            ticket_story_points = row_df["Custom field (Story Points)"][index]
            ticket_type = row_df["Issue Type"][index]
            labels = row_df["Labels"][index]
            components = row_df["Components"][index]
            epic_link = row_df["Epic Link Summary"][index]


            result = crew_agent(mini_df)
        # st.write(result)
            output_df = append_row(output_df,result,ticket_id,ticket_summary,ticket_description,ticket_story_points,ticket_type,labels,components,epic_link)
            output_df['ticket_url'] = output_df['Ticket Id'].apply(generate_url)

            output_df.insert(1, 'ticket_url', output_df.pop('ticket_url'))
        except Exception as err:
            result = [

                                    {
                        "is_summary_meaningful" : "Error in validating",
                        "is_summary_with_description_meaningful" : "Error in validating",
                        "is_summary_with_issuetype_meaningful" : "Error in validating",
                        "your_reason" : "Error in validating",
                    },
                    {
                        "is_description_present" : "Error in validating",
                        "is_description_meaningful" : "Error in validating",
                        "has_acceptance_criteria" :"Error in validating",
                        "new_description": "Error in validating",
                        "your_reason" :"Error in validating",
                    },
                    {
                        "is_story_points_present" :"Error in validating",
                        "is_story_points_meaningful" : "Error in validating",
                        "expected_story_points" :"Error in validating",
                        "your_reason" : "Error in validating",

                    },
                    {
                        "ticket_type" : "Error in validating",
                        "your_reason" : "Error in validating",

                    },
                    {
                        "is_label_present" : "Error in validating",
                    },
                    {
                        "is_component_present" : "Error in validating",
                    },
                    {
                        "is_epic_present" :"Error in validating",
                    }

                    ]
            output_df = append_row(output_df,result,ticket_id,ticket_summary,ticket_description,ticket_story_points,ticket_type,labels,components,epic_link)

            output_df['ticket_url'] = output_df['Ticket Id'].apply(generate_url)

            output_df.insert(1, 'ticket_url', output_df.pop('ticket_url'))
            print('Got error: ',err)


    # output_df.to_excel('Output.xlsx',index=False
    output_df_list_api.append(output_df.to_dict(orient="records")[0])

    # return output_df