import os
import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from supabase import create_client, Client
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_cx_tracker'

# Initialize Supabase Client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    selected_tag = request.args.get('tag', '').strip()
    
    # Base query for approved entries
    query = supabase.table('issues').select('*').eq('is_approved', True)
    
    if search_query:
        query = query.ilike('description', f'%{search_query}%')
    if selected_tag:
        query = query.eq('issue_type', selected_tag)
        
    issues_response = query.execute()
    issues = issues_response.data
    
    # Fetch sorting classifications for drop downs
    tags_response = supabase.table('tags').select('*').order('name').execute()
    tags = tags_response.data
    
    # Badge count logic for Admin queue
    queue_count = 0
    if session.get('logged_in'):
        queue_res = supabase.table('issues').select('id', count='exact').eq('is_approved', False).execute()
        queue_count = queue_res.count if queue_res.count is not None else 0
        
    return render_template('index.html', issues=issues, tags=tags, search_query=search_query, selected_tag=selected_tag, queue_count=queue_count)

@app.route('/admin/export-csv')
def export_csv():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Issue Type Tag', 'Short Description', 'Scope', 'Slack Link', 'Temporary Resolution', 'Status', 'Approval Status'])
    
    all_issues = supabase.table('issues').select('*').execute().data
    for issue in all_issues:
        status = 'Fixed' if issue['is_fixed'] else 'Not Fixed'
        approval = 'Approved' if issue['is_approved'] else 'Pending Review'
        cw.writerow([issue['id'], issue['issue_type'], issue['description'], issue['scope'], issue['slack_link'], issue['temp_solution'], status, approval])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=cx_issues_report.csv"
    output.headers["Content-Type"] = "text/csv"
    return output

@app.route('/admin/tags', methods=['GET', 'POST'])
def manage_tags():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        tag_name = request.form.get('tag_name', '').strip()
        if tag_name:
            check_existing = supabase.table('tags').select('*').eq('name', tag_name).execute().data
            if not check_existing:
                supabase.table('tags').insert({"name": tag_name}).execute()
                flash(f'Tag "{tag_name}" successfully added to the system.')
            else:
                flash('This classification tag already exists.')
        return redirect(url_for('manage_tags'))
        
    tags = supabase.table('tags').select('*').order('name').execute().data
    return render_template('tags.html', tags=tags)

@app.route('/admin/tags/delete/<int:tag_id>')
def delete_tag(tag_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    supabase.table('tags').delete().eq('id', tag_id).execute()
    flash('Tag removed from the platform.')
    return redirect(url_for('manage_tags'))

@app.route('/submit-issue', methods=['GET', 'POST'])
def submit_issue():
    if request.method == 'POST':
        supabase.table('issues').insert({
            "issue_type": request.form.get('issue_type'),
            "description": request.form.get('description'),
            "scope": request.form.get('scope'),
            "slack_link": request.form.get('slack_link'),
            "temp_solution": request.form.get('temp_solution'),
            "is_fixed": False,
            "is_approved": False
        }).execute()
        flash('Issue submitted successfully! It will appear on the dashboard once approved.')
        return redirect(url_for('index'))
        
    tags = supabase.table('tags').select('*').order('name').execute().data
    return render_template('submit.html', tags=tags)

@app.route('/add-entry', methods=['GET', 'POST'])
def add_entry():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        supabase.table('issues').insert({
            "issue_type": request.form.get('issue_type'),
            "description": request.form.get('description'),
            "scope": request.form.get('scope'),
            "slack_link": request.form.get('slack_link'),
            "temp_solution": request.form.get('temp_solution'),
            "is_fixed": 'is_fixed' in request.form,
            "is_approved": True
        }).execute()
        flash('Issue record published live!')
        return redirect(url_for('index'))
        
    tags = supabase.table('tags').select('*').order('name').execute().data
    return render_template('admin.html', tags=tags)

@app.route('/admin/queue')
def admin_queue():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    pending_issues = supabase.table('issues').select('*').eq('is_approved', False).execute().data
    return render_template('queue.html', issues=pending_issues)

@app.route('/admin/approve/<int:issue_id>')
def approve_issue(issue_id):
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    supabase.table('issues').update({"is_approved": True}).eq('id', issue_id).execute()
    return redirect(url_for('admin_queue'))

@app.route('/admin/reject/<int:issue_id>')
def reject_issue(issue_id):
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    supabase.table('issues').delete().eq('id', issue_id).execute()
    return redirect(url_for('admin_queue'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_data = supabase.table('users').select('*').eq('username', username).execute().data
        if user_data:
            user = user_data[0]
            if check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('index'))
                
        flash('Invalid verification credentials.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/toggle_fixed/<int:issue_id>')
def toggle_fixed(issue_id):
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
        
    issue = supabase.table('issues').select('*').eq('id', issue_id).execute().data[0]
    new_status = not issue['is_fixed']
    
    supabase.table('issues').update({"is_fixed": new_status}).eq('id', issue_id).execute()
    return redirect(url_for('index'))

@app.route('/delete_issue/<int:issue_id>')
def delete_issue(issue_id):
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    supabase.table('issues').delete().eq('id', issue_id).execute()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True,port=6969)