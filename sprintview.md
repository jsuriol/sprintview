# SPRINT VIEW
## A tool to view the progress of Agile sprints. 

## Table of Contents

- [Introduction](#Introduction)
- [Developer's Guide](#DeveloperGuide)
- [Scrum Master's Guide](#ScrumMasterGuide)
- [Appendix: Repo File Structure](#repofile)

## Introduction <a name="Introduction"></a>

The Sprint View tool runs on a browser and shows the progress of Agile sprints according to the information on our Gitlab
Sprint View project.  

This guide has two main sections: one for developers and one for scrum masters. Skip to the relevant one if you are 
familiar with the Agile method and the i5k Agile environment.

Sprint View doesn't survive communication failures with Gitlab's SprintView repo, and the program ends abruptly.  
Since it is rare, no friendlier remedy exists. It presents as server error and log entries to console 
and file provide additional information.  

<p align="center">*  *</p>


### The Agile Method
Agile is a way to organize software development around small steps and tackling only product functionality for which we have 
reasonable certainty it will be required.  

With this in mind we create a list of product features called the *backlog*. The primary requisite is that each feature be testable 
and demonstrable to the product owner, as evidence that each discrete effort adds a tangible functional element to the 
progress of the product. 

Each discrete effort is called a *sprint*, which has a fixed duration, a week, two, or longer.  We are currently using one-week sprints.  

We divide sprints into daily *scrums*, and during a daily *scrum meeting* we report the progress made on the previous work day.

During this meeting, each developer in the sprint reports:
	
+ Yesterday's progress,
	
+ Today's plan, and 

+ Blockers they might have.  

Sprints start with a meeting of the stake holders, the *Sprint Planning Meeting*, during which the Scrum Master decides which features from 
the backlog the next sprint will tackle, and whether to break down backlog features into tasks to better fit the sprint's duration. 
At the same time he assigns tasks to developers (or lets them choose) to complete during the sprint.  

At the end of the sprint a *Lessons-Learned-and-Recap Meeting* ends the sprint.  

There are several tools available, free and commercial, to jolly along the Agile sprint/scrum activities.  In the i5k project we use a 
GitLab Repo and a custom tool, Sprint View, described here. 

<p align="center">*  *</p>


## Developer's Guide <a name="DeveloperGuide"></a>

Developers usually attend the Sprint Planning meeting, when work gets assigned; then attend the daily scrum meeting at the 
appointed time, usually in a video call, or provide scrum updates in some other manner. At the end of the sprint 
the participants hold a lessons-learned-and-recap meeting, which marks the end of the sprint or carries any remaining work to the 
next sprint.  

In the i5k project we use a GitLab project and the Sprint View tool to submit scrum updates. 

Each feature in the backlog may become a sprint task or several; either way, as far as the sprint and 
Sprint View, a developer has one or more tasks to complete during a sprint. 

Each sprint task has also a corresponding GitLab Issue, identified by a number, for example, \#234.  

Therefore, a sprint task is the work a developer does related to an issue, there may be more than one task related to the 
same issue, beign worked on by different developers. Various developer tasks may refer to the same issue.

To submit the scrum update, follow these steps: 

+ Start Sprint View.

+ Click on the UPDATE button and then on your name in the drop-down list. 

+ This brings a page with the developer's task and their settings and editable fields for 'progress,' 'blocker,' and a 'today'
  checkbox to indicate the the developer is working on the task today.  

+ Fill as appropriate and click SEND.  

Use terse prose for task descriptions and blockers, lest they get truncated for display.  

Note:  The UPDATE button is available only when there is an open and active scrum.  

<p align="center">*  *</p>


## Scrum Master's Guide <a name="ScrumMasterGuide"></a>

Sprint View is a whole Django project contained in a single source file.  

 The whole package includes: 
 
 - the Django project file, *`sprintview.py`*, 
 - the installation requirements file,*`requirements.txt`*
 - a sample starter script, *`start.sh`*,
 - and this guide, *`sprintview.md`*. 
 
 To run Sprint View, once installed, you only need *`sprintview.py`*

### Installation

I assume installation takes place on a Linux, or Linux-like system.  

It requires Python 2.7.

The installation steps use a Python virtual environment, but Sprint View can install and run without it, if you can run pip with sudo 
to install the prerequisite modules.  

If you don't want to use a virtual environment skip to Step 2. 

Designate a working directory, I use '/home/user' in the examples.  


#### Installation Steps:

Step 1: Create a virtual environment. For example 'venv.'

    cd /home/user
    virtualenv venv
    source venv/bin/activate


Step 2: Move/download *`sprintview.py`* and *`requirements.txt`* into working dir and run:
 
    pip install -r requirements.txt 

 This installs Django 1.8.12, requests and beautifulsoup.

Once installed, before running Sprint View you must setup its data source, as described in the next sections. 

SprintView data can originate in a GitLab repo or in a local data file.  


##### Data File Access

Sprint View can get it's data source from a local file or Gitlab.  

If you have the file 'project_data' in the directory where Sprint View runs, the program assumes you 
want to use a local data store and the the file contains the appropriate json data. If you want to 
use another file you can do so by setting this variable. 

    export SPRINTVIEW_PATH=<path>

The data file must exist and contain json data, it cannot be empty. 

On start Sprint View tries to access the data file first, either as set in the SPRINTVIEW_PATH environment variable, 
or in the default path './project_data' in the current directory. If neither succeeds then it tries to get the 
project data from Gitlab, where our Sprintview project keeps the data this program reads and updates. 


#### Using Sprint View

To use Sprint View you need to first start the Sprint View server and then access it with a browser. 

Before you start the server you must set up the environment to let Sprint View know 
how to access its data source, as described in the previous two sections. 

To ensure direct connection to Gitlab, use a convenience script like this:

    #!/bin/bash 
    unset SPRINTVIEW_PATH
	mv ./project_data ./project_data.bak 2>/dev/null || true
    SPRINTVIEW_PATH=./project_data
    python sprintview.py runserver 0.0.0.0:8000

Remember to run the script like this: 

    source <script_name> 

The distribution has a sample script similar to this, named *`start.sh`*. 

This uses the Django development server, which is adequate for the task.  You can use Apache or other 
Web servers, but I will not get into the details here. 

Sprint View runs in DEBUG mode by default which is useful to troubleshoot.  

You can turn it DEBUG off with:

    export DEBUG=off 

before starting the server. 

Once the server runs, from a browser go to:

    <IP address/hostname>:8000 

This shows the last scrum of the last sprint.  Use the navigation buttons to view the sprint/scrum desired. The LAST button
takes you back to the last scrum of the last sprint, showing the most recent work.  

If changes are made to the scrum while Sprint View is running, you can tell Sprint View to reload the 
data source by clicking the RELOAD button.  

 The main view consists of five columns: developer, issue, task description today and work status. 

The DEV column header appears as a button, by default, while the other column headers appear as plain labels, but 
they are all clickable. Click any column header to turn it into a sort button and sort the view using the column as the key 
Cliking a sort button toggles the sort order between ascending and descending. 

Work status displays a progress bar for each task in the sprint.  The progress bar has two sections
The pale section represents the previous day's work and the darker section the work prior to that, if any. Each section contains a 
numeric percentage of the progress, with the total in bold at the end.  

In the even a scrum reports progress that is less than that of the previous day, a retrograde arrow shows the diminished progress. This 
can occur when a developer discovers that a task entails more work than they estimated.  

Work cycle: New Sprint -> Add Tasks -> [For each scrum] Update Scrum -> Close Scrum -> New Scrum [End For] -> Close Sprint.  

The admin button provides for these tasks, and has in addition a CLI button to enter ad hoc commands.  

CLI commands available are: 

+ -&lt;issue_id>          Removes all tasks with issue id <issue_id> from the active sprint.

+ -&lt;name>:&lt;issue_id>   Removes only the task with the task id given, which is made up of a name and an issue. 

+ sprm:&lt;number>        Deletes sprint number <number> 

+ scrm:&lt;number>        Deletes scrum number <number> 

+ spop                 Reopens the last sprint.

+ scop                 Reopens the last scrum. 

You can enter several commands in the same line separated by semicolons (';').   

The 'add_task' button, allows the entry of new tasks in addition to the pending tasks carried forward from sprint to sprint automatically.
To add tasks by the issue number just enter a comma-separated list of issue numbers.  

If a single issue must be divided into tasks by different developers, add the tasks like this, say we want have separate tasks for 
May, Monica, and Fish working on issue 999:  

    May:999,Monica:999,Fish:999

That would allow to track each effort independently of the others.  

<p align="center">*  *</p>



## Appendix: Repo file Structure<a name="repofile"></a>

The data file is a json hierarchy with project, sprint, tasks, and scrums as objects.  

Sprints have a header with a number and a date, and are ordered in increasing number and date order, which yield the same order. Immediately after 
the header a Sprint has a Task List, with a task count and a bullet list of tasks. After the Task List comes a series of Scrums. A Sprint 
represents a group of small steps to advance a project, and it primary purpose is to deliver one or more testable features successfully. Sprints usually 
last one or more weeks.  

A Scrum has a Header with its number. Scrums follow an increasing numeric order. A Scrum contains an expression of the work done by a team 
of developers in one day. The Scrum Master leads a daily Scrum Meeting to discuss the progress of the sprint tasks developers work on.

At this time no way to lock the Gitlab repo exist, programmatically, through the GitLab API, and thus serialize updates to the single file. 
If a collision occurs it may corrupt the repo file. Backups should exist in the /tmp directory of the recent Sprint View users. 

The Gitlab repo data file name is:  i5k_workspace_json

The /tmp backup copy of it is:  project_data.bak

There is no way to start a new project (sprint 1) other than to prune the json in the data file.  

To start a new project replace the old repo file with one containing this json:

    { 
        "name": "<project name>",
        "sprint_list": []
    }


<p align="center">*  *  *</p>