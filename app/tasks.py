from celery import shared_task
import boto3
from django.conf import settings
from utils.s3handler import read_file_from_s3
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.conf import settings
import pandas as pd
import requests
import json
import re
from io import StringIO
from transformers import GPT2Tokenizer
import tiktoken
import emoji
import openai
from tqdm import tqdm
import time
from openai import OpenAI
from datetime import datetime
import textwrap
import os
import io
from django.conf import settings
from django.template.loader import render_to_string


@shared_task
def process_file(email, username, file_name):
  print(f"Processing file: {file_name}")
  content = default_storage.open(file_name, 'r').read()
  process_tweets_to_pdf_report.delay(email, username, content)
  send_notification(
      to=email,
      subject="We've Got Your Tweet Data - JoyFuel Analysis Incoming!",
        template_file_name='app/analysis_started_notification.html',
        context= { "username": username }
  )
  default_storage.delete(file_name)


def test():
    text_stream = io.StringIO()
    text_stream.write("Test Output 1")
    text_stream.seek(0)
    attachments = [text_stream.read()]

    to = ["adebisijosephh@gmail.com"]
    subject = "We've Got Your Tweet Data - JoyFuel Analysis Incoming!"
    template = "app/analysis_started_notification.html"

    # subject = "Your JoyFuel Report is Ready – Discover Insights Within!"
    # template = "app/analysis_ended_notification.html"
    
    send_notification(
        to=to,
        subject=subject,
        template_file_name=template,
        context= {
            "username": "Dave"
        },
        attachments=attachments
    )

def send_notification(to, subject, template_file_name, context, attachments=[]):
    context['base_url'] = settings.BASE_URL
    html_content = render_to_string(template_file_name, context)
    receiptents = to
    if not isinstance(to, list):
        receiptents = [to]
    sendEmail(subject, receiptents, html_content, "", attachments)


def sendEmail(subject, to, html_content, text_content, attachments):
    from_mail = 'noreply@joyfuel.ai'  # Default from email
    email = EmailMultiAlternatives(subject, text_content, from_mail, to)
    email.attach_alternative(html_content, "text/html")
    for i in range(len(attachments)):
        email.attach(f'Joyfuel_report_{i}.pdf', attachments[i], 'application/pdf')
    email.send()


# Include all your necessary imports above

@shared_task
def process_tweets_to_pdf_report(email, username, json_content):
    
    # Begin Stage 1: Process Tweets
    def read_json_content_to_df(content):
        json_content = re.sub(r'window\.YTD\.tweets\.part0 = ', '', content)
        json_content = re.sub(r';$', '', json_content)
        data = json.loads(json_content)
        df = pd.json_normalize(data)
        return df

    df = read_json_content_to_df(json_content)
    print("Processed Tweet, df is returned")
    

    client = OpenAI(api_key=settings.OPENAI_KEY)
    print("Open AI Client is initiated")

    # List of columns to keep
    columns_to_keep = ['tweet.id_str', 'tweet.full_text', 'tweet.in_reply_to_status_id_str', 'tweet.in_reply_to_user_id_str', 'tweet.entities.user_mentions', 'tweet.entities.hashtags', 'tweet.created_at', 'tweet.retweet_count', 'tweet.favorite_count', 'tweet.lang', 'tweet.source']

    # Keep only the columns in the list
    df = df[columns_to_keep]
    print("Removes Unwanted Columns")

    # Initialize the tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    print("Initialize Tokenizer")

    # Function to count tokens in a text string
    def count_tokens(text):
        return len(tokenizer.encode(text))

    # Apply the function to the 'tweet.full_text' column to get the token count for each tweet
    df['tweet_token_count'] = df['tweet.full_text'].apply(count_tokens)
    print("Count Tokens in the text string")

    # Function to convert emojis to text
    def convert_emojis_to_text(text):
        return emoji.demojize(text)

    # Apply the function to the 'tweet.full_text' column to convert emojis to text
    df['Tweet full text XP'] = df['tweet.full_text'].apply(convert_emojis_to_text)
    print("Conver Emoji to text")

    prompt = """
    You are JoyFuel, an ultra-proficient language agent designed to detect and understand the underlying uses & gratifications millennials/ Gen Z use social media to sate. Below are the following tags you'd be looking for in each tweet-related text you are provided:
    Information Seeking tags: IS_News: Tweets providing news updates. IS_Edu: Educational content or factual information. IS_Data: Tweets containing data or statistics.
    Personal Identity tags: PI_PosSelf: Positive self-affirming tweets. PI_NegSelf: Negative self-affirming tweets. PI_Belief: Tweets expressing personal beliefs or values.
    Integration and Social Interaction tags: SI_Conv: Tweets initiating or continuing a conversation. SI_Ques: Tweets asking questions to the community. SI_Tag: Tweets tagging other users or groups.
    Entertainment tags: Ent_Humor: Tweets containing humor or jokes. Ent_Meme: Tweets sharing memes or other internet culture. Ent_FunFact: Tweets sharing fun facts or trivia.
    Emotional Release tags: ER_PosEmo: Tweets expressing or evoking positive emotions. ER_NegEmo: Tweets expressing or evoking negative emotions. ER_Rant: Tweets containing rants or venting.

    You would be supplied batch tweet data in this format:
    Tweet.id_str: 1671632499217252353
    Full text: RT @lumynous77: Twitter do your thing :folded_...

    Tweet.id_str: 1670513596315635712
    Full text: Listened to this album properly this weekend a...
    ...
    Supply your tag responses to each tweet in the following format:
    Tweet.id_str: 1671632499217252353
    laroye_tags: SI_tag, ER_PosEmo

    Tweet.id_str:  1670513596315635712
    laroye_tags: PI_Belief, ER_PosEmo

    """

    def format_tweets_for_batch(tweets_df):
        formatted_tweets = ""
        for _, row in tweets_df.iterrows():
            formatted_tweets += f"Tweet.id_str: {row['tweet.id_str']}\nFull text: {row['Tweet full text XP']}\n\n"
        return formatted_tweets

    def extract_tags_from_response(response_text):
        lines = response_text.split('\n')
        tags_dict = {}
        for i in range(0, len(lines), 3):
            if len(lines) > i and ": " in lines[i]:
                tweet_id = lines[i].split(": ")[1].strip()
            else:
                continue
            if len(lines) > i + 1 and ": " in lines[i + 1]:
                tags = lines[i + 1].split(": ")[1].strip()
            else:
                continue
            tags_dict[tweet_id] = tags
        return tags_dict

    def send_to_openai(prompt_to_send):
        while True:
            try:
                response = client.chat.completions.create(model="gpt-3.5-turbo-1106", messages=[{"role": "system", "content": prompt_to_send}])
                return response.choices[0].message.content

            except Exception as e:
                if "RateLimitError" in str(e):
                    print("Rate limit reached. Waiting for 60 seconds...")
                    time.sleep(60)  # sleep for 60 seconds before retrying
                else:
                    raise e

    print("Starting the tweet processing...")

    # Process tweets based on token counts
    token_sum = 0
    start = 0

    # Creating a progress bar for the main loop
    for end, row in tqdm(df.iterrows(), total=df.shape[0], desc="Batching Tweets"):
        token_sum += row['tweet_token_count']

        if token_sum > 1000:
            batch_df = df.iloc[start:end]

            # Format tweets for the batch with progress bar
            print("\nFormatting tweets for the batch...")
            formatted_tweets = format_tweets_for_batch(batch_df)

            # Sending the prompt to OpenAI with rate limit handling
            print("Sending the prompt to OpenAI...")
            prompt_to_send = prompt + formatted_tweets
            response_text = send_to_openai(prompt_to_send)

            # Extracting tags from the response
            print("Extracting tags from the response...")
            tags_dict = extract_tags_from_response(response_text.strip())

            # Updating the DataFrame with progress bar
            print("Updating the DataFrame...")
            for tweet_id, tags in tqdm(tags_dict.items(), desc="Updating DataFrame"):
                df.loc[df['tweet.id_str'] == tweet_id, 'laroye_tags'] = tags

            # Reset token_sum and update start
            token_sum = row['tweet_token_count']
            start = end

    print("\nInitial processing completed successfully!")

    def reprocess_skipped_rows(df):
        iteration_count = 0
        max_iterations = 3

        while df['laroye_tags'].isna().any() and iteration_count < max_iterations:
            print("\nReprocessing skipped rows...")

            skipped_rows = df[df['laroye_tags'].isna()]

            for index, row in tqdm(skipped_rows.iterrows(), total=skipped_rows.shape[0], desc="Reprocessing Skipped Rows"):
                # Format the tweet for sending
                formatted_tweet = f"Tweet.id_str: {row['tweet.id_str']}\nFull text: {row['Tweet full text XP']}\n\n"
                prompt_to_send = prompt + formatted_tweet

                # Sending the prompt to OpenAI with rate limit handling
                print("Sending the skipped tweet to OpenAI...")
                response_text = send_to_openai(prompt_to_send)

                # Extracting tags from the response
                print("Extracting tags from the response...")
                tags_dict = extract_tags_from_response(response_text.strip())

                # Updating the DataFrame
                print("Updating the DataFrame for skipped tweet...")
                if row['tweet.id_str'] in tags_dict:
                    df.loc[df['tweet.id_str'] == row['tweet.id_str'], 'laroye_tags'] = tags_dict[row['tweet.id_str']]

            print("\nReprocessing round completed. Checking for remaining skipped rows...")
            iteration_count += 1

        print("\nReprocessing finished after {} iterations.".format(iteration_count))

    # Call the reprocess function after the main loop
    reprocess_skipped_rows(df)

    print("\nAll processing, including reprocessing of skipped rows, completed successfully!")

    temp_df_stage1 = df.copy()

    #Stage 2
    def timed_operation(description, func, *args):
        start_time = time.time()
        print(f"Starting {description}...")
        result = func(*args)
        elapsed_time = time.time() - start_time
        print(f"Completed {description} in {elapsed_time:.2f} seconds.")
        return result

    def load_and_clean_data(df):
        df.dropna(subset=['laroye_tags'], inplace=True)
        return df

    def descriptive_analytics(df, prefixes):
        total_tweets = len(df)
        prefix_counts = {}
        for prefix in prefixes:
            count = df['laroye_tags'].str.contains(f"^{prefix}").sum()
            percentage = (count / total_tweets) * 100
            prefix_counts[prefix] = percentage
        return prefix_counts

    def extract_datetime_info(df):
        format_str = '%a %b %d %H:%M:%S %z %Y'
        df['hour'] = df['tweet.created_at'].apply(lambda x: datetime.strptime(x, format_str).hour)
        df['day_of_week'] = df['tweet.created_at'].apply(lambda x: datetime.strptime(x, format_str).strftime('%A'))
        return df

    def prescriptive_analytics(df, tags):
        results = {}
        for tag_group, tags_list in tags.items():
            group_df = df[df['laroye_tags'].str.contains('|'.join(tags_list))]
            top_days = group_df['day_of_week'].value_counts().nlargest(3).index.tolist()
            top_hours_by_day = {}
            for day in top_days:
                top_hours = group_df[group_df['day_of_week'] == day]['hour'].value_counts().nlargest(3).index.tolist()
                top_hours_by_day[day] = top_hours
            results[tag_group] = top_hours_by_day
        return results

    def get_top_ten_tag_groups(df):
        tag_group_counts = df['laroye_tags'].value_counts().nlargest(10)
        top_tag_groups = tag_group_counts.index.tolist()
        return top_tag_groups

    def prescriptive_analysis_top_tag_groups(df, top_tag_groups):
        top_tag_group_results = {}
        for tag_group in top_tag_groups:
            group_df = df[df['laroye_tags'] == tag_group]
            top_days = group_df['day_of_week'].value_counts().nlargest(3).index.tolist()
            top_hours_by_day = {}
            for day in top_days:
                top_hours = group_df[group_df['day_of_week'] == day]['hour'].value_counts().nlargest(3).index.tolist()
                top_hours_by_day[day] = top_hours
            top_tag_group_results[tag_group] = top_hours_by_day
        return top_tag_group_results

    def format_and_save_report(df, desc_analytics, presc_analytics, top_ten_tag_group_analytics):
        stream = io.StringIO()
        stream.write("Descriptive Analytics:\n")
        for prefix, percentage in desc_analytics.items():
            stream.write(f"{prefix}: {percentage:.2f}%\n")
        stream.write('\n')  # Additional newline for separation
        
        # Write Prescriptive Analytics
        stream.write("Prescriptive Analytics:\n")
        for group, analytics in presc_analytics.items():
            stream.write(f"\n{group}\n")  # Newline before and after group name
            for day, hours in analytics.items():
                hours_str = ', '.join(map(str, hours))
                stream.write(f"Top three hours for {day}: {hours_str}\n")

        # Write Top Ten Tag Groups Analytics
        stream.write("\nTop Ten Tag Groups:\n")  # Newline before subheading
        for tag_group, analytics in top_ten_tag_group_analytics.items():
            stream.write(f"\nTag Group: {tag_group}\n")  # Newline before and after tag group
            for day, hours in analytics.items():
                hours_str = ', '.join(map(str, hours))
                stream.write(f"Top three hours for {day}: {hours_str}\n")
        
        # Get the content of the stream
        content = stream.getvalue()
        stream.close()
        return content

    # Load and clean data
    df = timed_operation("loading and cleaning data", load_and_clean_data, temp_df_stage1)

    # Descriptive Analytics
    prefixes = ['IS_', 'PI_', 'SI_', 'ER_', 'Ent_']
    desc_analytics = timed_operation("descriptive analytics", descriptive_analytics, df, prefixes)

    # Extract DateTime Information
    df = timed_operation("extracting datetime information", extract_datetime_info, df)

    # Prescriptive Analytics
    tag_groups = {
        'Information group': ['IS_Edu', 'IS_Data', 'IS_News'],
        'Personal Identity group': ['PI_PosSelf', 'PI_Belief'],
        'Social Interaction group': ['SI_Conv', 'SI_Ques', 'SI_Tag'],
        'Entertainment group': ['Ent_Humor', 'Ent_Meme', 'Ent_FunFact'],
        'Emotional release group': ['ER_PosEmo', 'ER_Rant']
    }
    presc_analytics = timed_operation("prescriptive analytics", prescriptive_analytics, df, tag_groups)

    # Top Ten Tag Groups
    top_ten_tag_groups = get_top_ten_tag_groups(df)
    top_ten_tag_group_analytics = timed_operation("top ten tag groups analysis", prescriptive_analysis_top_tag_groups, df, top_ten_tag_groups)

    # Format and Save Report
    # output_file_path = 'file_2_tweet_analysis_report.txt'  # Modify as needed
    text_file_content = timed_operation("formatting and saving report", format_and_save_report, df, desc_analytics, presc_analytics, top_ten_tag_group_analytics)
    print("All processing complete.")

    stage3.delay(email, username, text_file_content)
        

#Stage 3
@shared_task
def stage3(email, username, text_file_content, fn_run_count=1):
    # Assuming you have already configured the OpenAI client with your API key
    client = openai.OpenAI(api_key=settings.OPENAI_KEY)

    # Create a new thread
    thread = client.beta.threads.create()

    # Create a new message within the thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content= text_file_content
    )

    # Execute the thread with specific instructions for the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=settings.ASSISTANT_ID,  # Replace with your actual assistant ID
    )

    # Function to download a binary file and write to local file system
    def download_file(file_id):
        # Get file content from OpenAI API
        response = client.files.content(file_id)
        return response.content

    def extract_file_id_using_regex(text_content):
        # Regex pattern to find "file_id="
        match = re.search(r'file_id=["\']([^"\']+)["\']', text_content)
        if match:
            # Extract and return the file_id
            return match.group(1)
        else:
            return None
        
    trials = 3
    while trials != 0:
        # Give a minute for run to complete
        time.sleep(180)
        # Fetch messages and extract the file ID
        messages = client.beta.threads.messages.list(
            thread_id=thread.id # Actual code that fetches messages goes here
        )
        if messages.data:
            text_content = str(messages.data[0].content)  # Extract text content from the first message
            file_id = extract_file_id_using_regex(text_content)  # Use regex to extract the file_id
            if file_id:
                file_content = download_file(file_id)  # Download the file
                send_notification(
                    to=email,
                    subject="Your JoyFuel Report is Ready – Discover Insights Within!",
                    template_file_name='app/analysis_ended_notification.html',
                    context= { "username": username},
                    attachments=[file_content]
                )
                return
            else:
                trials -= 1
                continue
                # raise ValueError("No file ID found in the text content.")
        else:
            if fn_run_count <= 3:
                stage3.delay(text_content, fn_run_count=fn_run_count + 1)
                break
            else:
                break
        
    if fn_run_count <= 3:
        stage3.delay(text_content, fn_run_count=fn_run_count + 1)
    else:
        print("Failed to process")
        # email notification for failed process.