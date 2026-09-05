import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from parser import parse_file
from pdf_generator import generate_html, build_pdf
import tempfile

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'dummy')
bot = telebot.TeleBot(BOT_TOKEN)

# In-memory storage for uploaded files per chat
user_data = {}

def get_session(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {'files': [], 'questions': [], 'state': 'uploading'}
    return user_data[chat_id]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Notes Generator Bot! Send me one or more .txt files. When you are done, send /done.\nYou can send /cancel at any time to clear uploaded files and restart.")
    get_session(message.chat.id)

@bot.message_handler(commands=['cancel'])
def cancel_process(message):
    if message.chat.id in user_data:
        del user_data[message.chat.id]
    get_session(message.chat.id)
    bot.reply_to(message, "Process cancelled. All uploaded files have been cleared. Send a .txt file to start over.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    session = get_session(message.chat.id)
    if message.document.mime_type != 'text/plain' and not message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "Please upload a .txt file.")
        return
        
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        text = downloaded_file.decode('utf-8')
        
        parsed_qs = parse_file(text)
        if not parsed_qs:
            bot.reply_to(message, "Could not find any questions in this file. Please check the format.")
            return
            
        session['questions'].extend(parsed_qs)
        session['files'].append(message.document.file_name)
        
        bot.reply_to(message, f"Received '{message.document.file_name}'. Parsed {len(parsed_qs)} questions. Send more files or /done.")
    except Exception as e:
        bot.reply_to(message, f"Error processing file: {str(e)}")

def send_generated_files(chat_id, questions, title_prefix="notes"):
    html_content = generate_html(questions)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = os.path.join(tmpdir, f"{title_prefix}.html")
        pdf_path = os.path.join(tmpdir, f"{title_prefix}.pdf")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        build_pdf(html_content, pdf_path)
        
        with open(pdf_path, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"PDF: {title_prefix}")
        with open(html_path, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"HTML: {title_prefix}")

@bot.message_handler(commands=['done'])
def done_uploading(message):
    session = get_session(message.chat.id)
    if not session['questions']:
        bot.reply_to(message, "You haven't uploaded any valid .txt files yet.")
        return
        
    bot.reply_to(message, f"Processing {len(session['questions'])} total questions...")
    
    try:
        # Sort questions by num just in case
        questions = sorted(session['questions'], key=lambda x: x['num'])
        send_generated_files(message.chat.id, questions, "full_notes")
        
        # Ask about ranges
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Yes", callback_data="range_yes"),
            InlineKeyboardButton("No", callback_data="range_no")
        )
        bot.send_message(message.chat.id, "Do you want to generate PDFs for specific ranges?", reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"Error generating files: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data in ["range_yes", "range_no"])
def handle_range_prompt(call):
    if call.data == "range_no":
        bot.edit_message_text("Process completed. Send /start to begin a new session.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        if call.message.chat.id in user_data:
            del user_data[call.message.chat.id]
    else:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("One range", callback_data="type_one_range"),
            InlineKeyboardButton("Full range", callback_data="type_full_range")
        )
        bot.edit_message_text("Select range type:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["type_one_range", "type_full_range"])
def handle_range_type(call):
    session = get_session(call.message.chat.id)
    if call.data == "type_one_range":
        session['state'] = 'wait_one_range'
        bot.edit_message_text("Send ranges separated by comma (e.g. '1-10, 11-20, 50-60'):", chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        session['state'] = 'wait_full_range'
        bot.edit_message_text("Send the number of questions per PDF (e.g. '5'):", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.message_handler(func=lambda message: get_session(message.chat.id).get('state') == 'wait_one_range')
def handle_one_range(message):
    session = get_session(message.chat.id)
    text = message.text
    parts = [p.strip() for p in text.split(',')]
    
    all_qs = {q['num']: q for q in session['questions']}
    
    for part in parts:
        if '-' in part:
            try:
                s, e = map(int, part.split('-'))
                s, e = min(s, e), max(s, e)
                range_qs = [all_qs[n] for n in range(s, e + 1) if n in all_qs]
                if range_qs:
                    send_generated_files(message.chat.id, range_qs, f"notes_{s}_{e}")
            except Exception:
                bot.reply_to(message, f"Invalid format in range part: {part}")
        else:
            try:
                n = int(part)
                if n in all_qs:
                    send_generated_files(message.chat.id, [all_qs[n]], f"notes_{n}")
            except Exception:
                bot.reply_to(message, f"Invalid format in range part: {part}")
                
    bot.reply_to(message, "Range generation completed. Send /start to begin again.")
    session['state'] = 'uploading'
    
@bot.message_handler(func=lambda message: get_session(message.chat.id).get('state') == 'wait_full_range')
def handle_full_range(message):
    session = get_session(message.chat.id)
    try:
        chunk_size = int(message.text.strip())
        if chunk_size <= 0:
            raise ValueError()
    except Exception:
        bot.reply_to(message, "Please enter a valid positive integer.")
        return
        
    questions = sorted(session['questions'], key=lambda x: x['num'])
    for i in range(0, len(questions), chunk_size):
        chunk = questions[i:i + chunk_size]
        min_n = chunk[0]['num']
        max_n = chunk[-1]['num']
        send_generated_files(message.chat.id, chunk, f"notes_{min_n}_to_{max_n}")
        
    bot.reply_to(message, "Full range generation completed. Send /start to begin again.")
    session['state'] = 'uploading'
