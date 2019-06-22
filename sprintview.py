'''
    sprintview.py
    -------------

    Shows a status board for the sprints and scrums of an Agile project.

    Both parts of a Django project front-end and back-end
    are in one file, this file.

    For usage details see sprintview.md

    Program strategy:

      - Read the data source, repo or file (repo class).  At present in a Gitlab project.
      - Create objects to represent the repo data, sprints, tasks, scrums, etc.
      - Render a view of the current sprint and scrum.

    Main objects:

        Repo: Class to obtain the project data from Gitlab or a local file.

        Project:  A collection of Sprints under a project name.

        Sprint: A collection of SprintTasks, and Scrums.  Has also a sprint number and start date.

        SprintTask: A piece of work assigned to a developer.

        Scrum:  A collection of scrum updates (ScrumTask).

        ScrumTask:  A developer's update to a SprintTask.

        View: A view is defined by a sprint number, a scrum number, a sort column, and a sort order.

    Once a view, as defined by the tuple above, has been generated, it is cached
    to a memory cache and retrieved on demand.

    Work cycle:

        New Sprint/Add Tasks/Update/Close Scrum/New Scrum/Update/Close Sprint

    All operational data is kept in memory.

    Uses Gitlab API to read and write Gitlab objects.

    Uses HTML and CSS only, no JS, JQuery, etc.

    See sprintview.md for more details.

    For developers names, internally uses Gitlab login ids, and externally, if supplied in start.sh,
    uses a lookup table to convert names to login ids.  For input, names are case insensitive, but for
    output are always capitalized.

'''

from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application
from django.template import Context, Template
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls import url
import datetime
import StringIO
import requests
import logging
import base64
import time
import json
import sys
import ast
import re
import os

#
#  Globals
#
proj   = None  # Umbrella data container.
view   = None  # Display HTML page data and vars.
inited = False # Server just up.

#
#  HTML Template
#
#  Main app page.
#
#  Uses a series of flex containers
#
page = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    /*
     *  CSS Reset
     */
	html, body, div, span, applet, object, iframe,
	h1, h2, h3, h4, h5, h6, p, blockquote, pre,
	a, abbr, acronym, address, big, cite, code,
	del, dfn, em, img, ins, kbd, q, s, samp,
	small, strike, strong, sub, sup, tt, var,
	b, u, i, center,
	dl, dt, dd, ol, ul, li,
	fieldset, form, label, legend,
	table, caption, tbody, tfoot, thead, tr, th, td,
	article, aside, canvas, details, embed,
	figure, figcaption, footer, header, hgroup,
	menu, nav, output, ruby, section, summary,
	time, mark, audio, video {
		margin: 0;
		padding: 0;
		border: 0;
		font-size: 100%;
		font: inherit;
		vertical-align: baseline;
	}
	/* HTML5 display-role reset for older browsers */
	article, aside, details, figcaption, figure,
	footer, header, hgroup, menu, nav, section {
		display: block;
	}
	body {
		line-height: 115%;
	}
	ol, ul {
		list-style: none;
	}
	blockquote, q {
		quotes: none;
	}
	blockquote:before, blockquote:after,
	q:before, q:after {
		content: '';
		content: none;
	}
	table {
		border-collapse: separate;
		border-spacing: 0.1em;
	}

    /*  End CSS Reset   */

    html, body {
        height: 98%;
        margin: 0;
        padding: 0;
		font-size: 100%;
        font-family: arial;
        font-family: TimesNewRoman;
        font-size: 1em;
        /*border: 2px solid blue;*/
    }
    body {
        display: flex;
        -webkit-display: flex;
        flex-direction: column;
        -webkit-flex-direction: column;
        align-items: center;
        -webkit-align-items: center;
        justify-content: center;
        -webkit-justify-content: center;
        color:#660000;
        background-color:#fffae6;
        /*border: 2px solid black;*/
    }
    /*
     *  Three main div: top_frame, middle_flame, and bottom frame.
     */
    .top_frame {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 22%;
        display: flex;
        -webkit-display: flex;
        flex-direction: column;
        -webkit-flex-direction: column;
        justify-content: flex-start;
        -webkit-justify-content: flex-start;
        align-items: center;
        -webkit-align-items: center;
        margin: 0;
        padding: 0;
        z-index: 1;
        /*border: 2px solid red;*/
    }
    .mid_frame {
        position: fixed;
        top: 21.5%;
        left: 1%;
        height: {{ mid_height }}%;
        margin-bottom: .5%;
        width: 99%;
        display: flex;
        -webkit-display: flex;
        overflow-y: auto;
        -webkit-overflow-y: auto;
        flex-direction: column;
        -webkit-flex-direction: column;
        align-items: center;
        -webkit-align-items: center;
        /*border: 2px solid green;*/
    }
    .bottom_frame {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: {{ bot_height }}%;
        display: flex;
        -webkit-display: flex;
        flex-direction: column;
        -webkit-flex-direction: column;
        align-items: center;
        -webkit-align-items: center;
        padding: 0;
        overflow-y: auto;
        -webkit-overflow-y: auto;
        /*border-top: 1px solid pink;*/
    }
    /*
     *  top_frame  ------------------------------------------
     */
    .title_header {
        align-self: center;
        margin: 0;
        padding: 0;
        margin-top: 10px;
        font-weight:bold;
        font-size: 1.3em;
        /*border: 2px solid red;*/
    }
    .button_wrap {
        width: 80%;
        display: flex;
        -webkit-display: flex;
        justify-content: flex-end;
        -webkit-justify-content: flex-end;
        /*border: 1px solid orange;*/
    }
    .admin_dropdown {
        width: 12%;
        height: 100%;
        display: flex;
        -webkit-display: flex;
        align-items: center;
        -webkit-align-items: center;
        margin-right: 65%;
        z-index: 99999;
        /*border: 1px solid blue;*/
    }
    .admin_button {
        width: 100%;
        border-radius: 15%;
        color: white;
        background: linear-gradient(#737373, #bfbfbf);
        font-size: 1em;
        cursor: pointer;
        box-shadow: 0 2px #999;
    }
    .admin_dropdown_content {
        position: absolute;
        top: 35%;
        min-width: 10%;
        display: flex;
        -webkit-display: flex;
        flex-direction: column;
        -webkit-flex-direction: column;
        visibility: hidden;
        background-color: #f9f9f9;
        box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
        z-index: 9999;
    }
    .admin_dropdown_content a {
        color: black;
        padding: 12px 16px;
        text-decoration: none;
    }
    .admin_dropdown_content a:hover {
        background-color: #f1f1f1
    }
    .admin_dropdown:hover .admin_dropdown_content {
        visibility: visible;
    }
    .admin_dropdown:hover .admin_button {
        background-color: #3e8e41;
    }
    .last_button {
        width: 12%;
        margin-right: 2%;
        color:white;
        background: linear-gradient(#6699cc, #b3cce6);
        font-size: 1em;
        cursor: pointer;
        border-radius: 15%;
        box-shadow: 0 2px #999;
    }
    .reload_button {
        width: 12%;
        margin-right: 2%;
        color:white;
        background: linear-gradient(#3973ac, #8cb3d9);
        font-size: 1em;
        cursor: pointer;
        border-radius: 15%;
        box-shadow: 0 2px #999;
    }
    .update_dropdown {
        width: 12%;
        display: flex;
        -webkit-display: flex;
        align-items: center;
        -webkit-align-items: center;
        /*border: 1px solid red;*/
    }
    .update_button {
        width: 100%;
        color: white;
        background: linear-gradient(#39ac39, #79d279);
        font-size: 1em;
        cursor: pointer;
        border-radius: 15%;
        box-shadow: 0 2px #999;
    }
    .update_dropdown_content {
        position: absolute;
        top: 35%;
        min-width: 10%;
        display: flex;
        -webkit-display: flex;
        flex-direction: column;
        -webkit-flex-direction: column;
        visibility: hidden;
        background-color: #f9f9f9;
        box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
    }
    .update_dropdown_content a {
        padding: 12px 16px;
        color: black;
        text-decoration: none;
    }
    .update_dropdown_content a:hover {
        background-color: #f1f1f1
    }
    .update_dropdown:hover .update_dropdown_content {
        {% if scrum_active %}
            visibility: visible;
        {% else %}
            visibility: hidden;
        {% endif %}
    }
    .update_dropdown:hover .update_button {
        background-color: #3e8e41;
    }
    .nav_container {
        width: 95%;
        height: 30%;
        display: flex;
        -webkit-display: flex;
        align-items: center;
        -webkit-align-items: center;
        margin-top: 5%;
        /*border: 1px solid purple;*/
    }
    .sprint_nav_frame, .scrum_nav_frame {
        display: flex;
        -webkit-display: flex;
        align-items: center;
        -webkit-align-items: center;
        /*border: 2px solid orange;*/
    }
    .sprint_nav_frame {
        width: 100%;
        margin-left: 25%;
    }
    .scrum_nav_frame {
        width: 100%;
        margin-left: 7%;
    }
    .scrum_nav_header {
        font-size: 1.5em;
        font-weight: bold;
    }
    .scrum_nav_buttons {
        padding-left: 2%
    }
    .scrum_nav {
        background-color: #ffeb99;
        font-size: 1.7em;
    }
    .noscrum {
        font-size: 1.2em;
        font-family: helvetica;
    }
    .sprint_nav_header {
        font-size: 1.1em;
        font-weight: bold;
    }
    .sprint_nav_buttons {
        padding-left: 2%
    }
    .sprint_nav {
        background-color: #fff0b3;
        font-size: 1.0em;
    }
    .sprint_nav, .scrum_nav {
        border: none;
        padding: 4px 8px;
        color:#660000;
        text-align: center;
        margin: 4px 2px;
        font-family: monospace;
        cursor: pointer;
        border-radius: 50%;
        box-shadow: 0 1px #999;
        transition-duration: 0.4s;
    }
    .sprint_nav:hover, .scrum_nav:hover {
        background-color: #ffd633;
    }
    .sprint_nav:active, .scrum_nav:active, .last:active {
        background-color: #ffe680;
        box-shadow: 0 1px #666;
        transform: translateY(2px);
    }
    .date {
       margin-left: 2%;
       /*border: 2px solid yellow;*/
    }
    .tab_head {
        width: 60%;
        display: flex;
        -webkit-display: flex;
        align-self: flex-start;
        -webkit-align-self: flex-start;
        justify-content: flex-start;
        -webkit-justify-content: flex-start;
        padding: 0px;
        padding-top: 13%;
        margin-left: 9.8%;
        /*border: 2px solid purple;*/
    }
    .dev_sort, .issue_sort, .desc_sort, .status_sort {
        color:#660000;
        border: none;
        background:none;
        outline: none;
        /*border: 2px solid lightcoral;*/
    }
    .dev_sort {
        margin-left:0.4%;
    }
    .issue_sort {
        margin-left:2.5%;
    }
    .desc_sort {
        margin-left:18%;
    }
    .status_sort {
        margin-left:45%;
    }
    .separator {
        width: 85%;
        padding:0px;
        margin: 0px;
        color: darkred;
        margin-top: 1px;
        /*border: 1px solid green;*/
    }

    /*  End of top_frame  */

    /*
     *  middle_frame  ------------------------------------------
     */

    .table_div {
        display: flex;
        -webkit-display: flex;
        justify-content: flex-end;
        -webkit-justify-content: flex-end;
        /*border: 2px solid aqua;*/
    }
    .scrum {
        width: 91%;
        table-layout: fixed;
        white-space: nowrap;
        /*border: 2px solid purple;*/
    }
    .scrum td {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        -webkit-overflow: hidden;
    }
    /* Column widths are based on these 4 cells */
    .dev {
        width: 7%;
    }
    .isssue {
        width: 7%;
    }
    .desc {
        width: 30%;
        padding-right: 5%;
    }
    .status {
        width: 56%;
        padding-right: 5%;
    }
    .row1 {
        background: #ffecb3;
    }
    .row2 {
        background: #fff2cc;
    }
    .f1, .f2 {
        text-align: center;
    }
    .f3, .f4 {
        text-align: left;
    }
    .f1, .f2, .f3 {
        font-size: 1.0em;
    }
    .f4 {
        background: #fffae6;
    }

    /*  End of middle_frame  */

    /*
     *  bottom_frame   ------------------------------------------
     */

    .bottom_wrapper {
        width: 100%;
        display: flex;
        -webkit-display: flex;
        align-self: flex-start;
        -webkit-align-self: flex-start;
        overflow-y: auto;
        -webkit-overflow-y: auto;
        /*border-top: 2px solid red;*/
    }
    .blk_header {
        margin: 0;
        margin-left: 140px;
        align-self: flex-start;
        -webkit-align-self: flex-start;
        /*border: 2px solid tan;*/
    }
    .blk_scroll {
        width: 100%;
        overflow-y: auto;
        -webkit-overflow-y: auto;
    }
    .blockers_div {
        width: 90%;
        margin: 0;
        margin-left: 5px;
    }
    .blockers_list {
        margin: 0;
        font-size: 0.9em;
        /*border: 2px solid lightcoral;*/
    }

    /*  End of bottom_frame  ------------------------------------- */

    /*
     *  Text coloring.
     */
    mark.dark {
        color:#203f60;
        background: none;
        font-weight:bold;
        font-family: monospace;
        font-size: 1.3em
    }
    mark.medium {
        color:#ffffff;
        background: #538ac6;
        font-family: monospace;
        font-size: 1.3em
    }
    mark.light {
        color:#203f60;
        background: #c8d9ea;
        font-family: monospace;
        font-size: 1.3em
    }
    mark.dark_red {
        color:#cc0000;
        background: none;
    }
    mark.help_eg {
        color:black;
        background: white;
    }
    mark.red {
        color:#ff3300;
        background: none;
        font-family: "Helvetica Narrow";
    }
    mark.orange {
        color:#ff8533;
        background: none;
        font-weight:bold;
        font-family: monospace;
        font-size: 1.3em
    }
    mark.today {
        text-decoration: underline;
        background: #ffff80;
    }

    /*
     *  Shading of sorting labels.
     */
    .{{ sort_column }} {
        {% if sort_order == "ascending" %}
            background: linear-gradient(#ffcc00, #fffae6);
        {% else %}
            background: linear-gradient(#fffae6, #ffcc00);
        {% endif %}
    }

    /*
     *  Addtasks and CLI modal dialog.
     */
    .modalDialog {
        position: fixed;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        font-family: Arial, Helvetica, sans-serif;
        background: rgba(0,0,0,0.8);
        opacity:0;
        -webkit-transition: opacity 400ms ease-in;
        -moz-transition: opacity 400ms ease-in;
        transition: opacity 400ms ease-in;
        pointer-events: none;
        z-index: 99999;
    }
    .modalDialog:target {
        opacity:1;
        pointer-events: auto;
    }
    .modalDialog > div {
        width: 650px;
        position: relative;
        margin: 10% auto;
        padding: 10px 20px 13px 20px;
        border-radius: 10px;
        background: #fff;
        background: -moz-linear-gradient(#fff, #999);
        background: -webkit-linear-gradient(#fff, #999);
        /*#background: -o-linear-gradient(#fff, #999);*/
    }
    .close {
        position: absolute;
        top: -10px;
        right: -12px;
        width: 24px;
        line-height: 25px;
        color: #FFFFFF;
        background: #606061;
        text-align: center;
        text-decoration: none;
        font-weight: bold;
        -webkit-border-radius: 12px;
        border-radius: 12px;
        -webkit-box-shadow: 1px 1px 3px #000;
        box-shadow: 1px 1px 3px #000;
    }
    .close:hover {
        background: #00d9ff;
    }
    .taskadd {
        width: 85%;
        height: 30px;
        font-family: monospace;
        color: black;
        background: white;
    }
    .cliClose {
        position: absolute;
        top: -10px;
        right: -12px;
        width: 24px;
        line-height: 25px;
        color: #FFFFFF;
        background: #606061;
        text-align: center;
        text-decoration: none;
        font-weight: bold;
        -webkit-border-radius: 12px;
        border-radius: 12px;
        -webkit-box-shadow: 1px 1px 3px #000;
        box-shadow: 1px 1px 3px #000;
    }
    .cliClose:hover {
        background: #00d9ff;
    }
    .clitext {
        width: 85%;
        height: 30px;
        font-family: monospace;
        color: black;
        background: white;
    }
    .modal_title {
        font-size: 1.5em;
        font-weight: bold;
        margin-bottom: 8%;
    }
    .help {
        font-size: 1em;
        font-family: monospace;
    }
</style>
    <title>SPRINT VIEW</title>
</head>
<body>
    <div class=top_frame>

        <h2 class="title_header">SPRINT VIEW</h2>

        <div class="button_wrap">
            <div class="admin_dropdown">
                <button class="admin_button">ADMIN</button>
                <div class="admin_dropdown_content">
                    {% if scrum_on %}
                        <a href="#" onclick="location.href='/close_scrum'">Close Active Scrum</a>
                    {% endif %}
                    {% if sprint_on %}
                        <a href="#" onclick="location.href='/close_sprint'">Close Active Sprint</a>
                    {% endif %}
                    {% if sprint_on and not scrum_on %}
                        <a href="#" onclick="location.href='/new_scrum'">New Scrum</a>
                    {% endif %}
                    {% if not scrum_on and not sprint_on %}
                        <a href="#" onclick="location.href='/new_sprint'">New Sprint</a>
                    {% endif %}
                    {% if sprint_on %}
                        <a href="#task_add">Add Tasks</a>
                    {% endif %}
                        <a href="#cli">CLI</a>

                </div>
            </div>
            <button class="last_button" onclick="location.href='/last'">LAST</button>
            <button class="reload_button" onclick="location.href='/reload'">RELOAD</button>
            <div class="update_dropdown">
                <button class="update_button">UPDATE</button>
                <div class="update_dropdown_content">
                    {% for dev in dev_list %}
                        <a href="#" onclick="window.location.replace('/devel_{{ dev }}');" target="_self">{{ dev}} </a>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div class="nav_container">
            <div class="scrum_nav_frame">
                <h2 class="scrum_nav_header"> Scrum: {{ scrum_num }} of {{ num_scrums }}</h2>
                <div class="scrum_nav_buttons">
                    <button class="scrum_nav" onclick="location.href='/prev_scrum'">&lt;</button>
                    <button class="scrum_nav" onclick="location.href='/next_scrum'">&gt;</button>
                </div>
                {% if not scrum_active %}
                    <p class="noscrum">&nbsp;&nbsp;<mark class="red">No Active Scrum</mark></p>
                {% endif %}
            </div>

            <div class="sprint_nav_frame">
                <h3 class="sprint_nav_header"> Sprint: {{ sprint_num }} of {{ num_sprints }}</h3>
                <div class="sprint_nav_buttons">
                    <button class="sprint_nav" onclick="location.href='/prev_sprint'">&lt;</button>
                    <button class="sprint_nav" onclick="location.href='/next_sprint'">&gt;</button>
                </div>
                <p class="date">Started: {{ sprint_date }}&nbsp;&nbsp;&nbsp;&nbsp; Tasks: {{ num_tasks }}</p>
            </div>
        </div>
        <div class="tab_head">
            <button class="dev_sort" onclick="location.href='/dev_sort'">DEVELOPER</button>
            <button class="issue_sort" onclick="location.href='/issue_sort'">ISSUE</button>
            <button class="desc_sort" onclick="location.href='/desc_sort'">DESCRIPTION</button>
            <button class="status_sort" onclick="location.href='/status_sort'">STATUS</button>
        </div>
        <hr class="separator">
    </div> <!-- Top Frame  -->
    <div class="mid_frame">

        <div class="table_div">
            <table class="scrum">
                <thead>
                   <tr>
                       <th class="dev"></th>
                       <th class="issue"></th>
                       <th class="desc"></th>
                       <th class="status"></th>
                   </tr>
                </thead>
                <tbody>
                    {% for task in task_list %}
                       <tr class="{% cycle 'row1' 'row2' %}">
                           <td class="f1">{{ task.0 }}</td>
                           <td class="f2">{% autoescape off %}{{ task.1 }}{% endautoescape %}</td>
                           <td class="f3">{% autoescape off %}{{ task.2 }}{% endautoescape %}</td>
                           <td class="f4">{% autoescape off %}{{ task.3 }}{% endautoescape %}</td>
                       </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div> <!-- Table Div  -->

    </div>  <!-- Mid Frame  -->
    <div class="bottom_frame">
        <hr class="separator">
        <div class="bottom_wrapper">
            <h4 class="blk_header">{{ blk_label }}</h4>
            {% if blk_list %}
                <div class="blk_scroll">
                    <div class="blockers_div">
                        <ol class="blockers_list">
                            {% for blk in blk_list %}
                                <li>{% autoescape off %}{{ blk }}{% endautoescape %}</li>
                            {% endfor %}
                        </ol>
                    </div> <!-- Blockers Div  -->
                </div>
            {% endif %}
        </div>
    </div>
    <div id="task_add" class="modalDialog">
        <div>
            <a href="#close" title="Close" class="close">X</a>
            <h2 class="modal_title">Add Tasks</h2>
            <p style="font-size: .9em">Enter a comma separated list of issue numbers to add tasks to active sprint.</p>
            <form action="/task_add" autocomplete="on">
                <input type="text" class="taskadd" maxlength="200" name="issue_list" autocomplete="on">
                <input type="submit" value="Submit">
            </form>
            <pre class="help">

        Examples:

          - To add issues as assigned:        <mark class="help_eg"> 234,235,238,243      </mark>

          - To assign and add issues:         <mark class="help_eg"> Monica:234,Chris:235 </mark>

          - To share issues: e.g. issue 257   <mark class="help_eg"> Chris:257,Monica:257 </mark>
            </pre>
        </div>
    </div>
    <div id="cli" class="modalDialog">
        <div>
            <a href="#close" title="Close" class="cliClose">X</a>
            <h2 class="modal_title" >CLI</h2>
            <form action="/cli" autocomplete="on">
                <input type="text" class="clitext" maxlength="200" name="cli_text" autocomplete="on">
                <input type="submit" value="Submit">
            </form>
            <pre class="help">

       Format: one or more commands separated by semicolons (';')

       Commands:

          <mark class="help_eg"> sprm:&lt;num&gt;    </mark>  Remove sprint number &lt;num&gt;.

          <mark class="help_eg"> scrm:&lt;num&gt;    </mark>  Remove scrum number &lt;num&gt;.

          <mark class="help_eg"> spop          </mark>  Re-open last sprint.

          <mark class="help_eg"> scop          </mark>  Re-open last scrum.

          <mark class="help_eg"> -&lt;num&gt;        </mark>  Remove all sprint tasks with issue &lt;num&gt;.

          <mark class="help_eg"> -&lt;name&gt;:&lt;num&gt; </mark>  Remove task with developer &lt;name> and issue &lt;num&gt;.
            </pre>
        </div>
    </div>
</body>
</html>
'''

#
#  Page for developer updates.
#
update_page = '''
<!DOCTYPE html>
<html>
<head>
<style>
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    /* Remove formatting from links*/

    a {
        color: inherit;
    }
    html {
        width: 100%;
        height: 100%;
    }
    body {
        width: 100%;
        height: 100%;
        display: flex;
        -webkit-display: flex;
        flex-direction: column;
        -webkit-flex-direction: column;
        align-items: center;
        -webkit-align-items: center;
        justify-content: center;
        -webkit-justify-content: center;
        color:#4d0000;
        background-color:#fffae6;
    }
    .close {
        position: absolute;
        top: 12.5%;
        right: 7.7%;
        z-index: 9;
    }
    .upform {
        width: 100%;
        height: 100%;
        display: flex;
        -webkit-display: flex;
        flex-direction: column;
        -webkit-flex-direction: column;
        align-items: center;
        -webkit-align-items: center;
        /*border: 2px solid green;*/
    }
    .fixed  {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 16%;
        display: flex;
        -webkit-display: flex;
        flex-direction: column;
        -webkit-flex-direction: column;
        align-items: center;
        -webkit-align-items: center;
        justify-content: center;
        -webkit-justify-content: center;
        padding-bottom: 1.5%;
        background: #fff5cc;
        /*border: 2px solid red;*/
    }
    .nav {
        width: 100%;
        height: 50%;
        display: flex;
        -webkit-display: flex;
        justify-content: flex-start;
        -webkit-justify-content: flex-start;
        /*border: 2px solid cyan;*/
    }
    .submit {
        width:  10%;
        margin-left:auto;
        margin-right:5%;
        margin-bottom:15%;
        color:#0f3e0f;
        background: linear-gradient(#85e085, #d6f5d6);
        border-radius: 12%;
        font-size: 0.9em;
        padding: 2%;
        cursor: pointer;
        box-shadow: 0 2px #999;
    }
    .scrum {
        width:82%;
    }
    .cancel {
        width: 10%;
        margin-left:5%;
        margin-bottom:15%;
        border-radius: 12%;
        padding: 2%;
        color:#660000;
        background: linear-gradient(#ffeb99, #fffae6);
        font-size: 0.81em;
        cursor: pointer;
        box-shadow: 0 2px #999;

    }
    .cont {
        position: fixed;
        top: 16%;
        left: 0;
        width: 100%;
        height: 80%;
        display: flex;
        -webkit-display: flex;
        overflow-y: auto;
        -webkit-overflow-y: auto;
        flex-direction: column;
        -webkit-flex-direction: column;
        align-items: center;
        -webkit-align-items: center;
        /*border: 2px solid blue;*/
    }
    .cont2 {
        width: 90%;
        display: flex;
        -webkit-display: flex;
        flex-direction: column;
        -webkit-flex-direction: column;
        justify-content: center;
        -webkit-justify-content: center;
        padding: 2%;
        margin: 0;
        margin-top: 2%;
        /*border: 2px solid yellow;*/
    }
    .progress {
        width: 3em;
        height: 2em;
        margin-right: 2%;
        color: #330000;
        font-size: 1.0em;
    }
    .today {
        width: 3%;
        margin-right: 2%;
    }
    .blocker {
        width: 70%;
        height: 2.1em;
        font-size: 0.9em;
        color: #330000;
    }
    h3 {
        align: center;
        margin-top: 3%;

    }
    input, textarea {
        color:#660000;
        background-color : #fff0b3;
    }
    fieldset {
        border: 1px solid #990000;
        margin-bottom: {{ interfield }}px;
    }
</style>
<script>
    var backbutton = document.getElementById("backButton");
    backbutton.onclick = function(e){
        e = e || window.event; // support  for IE8 and lower
        e.preventDefault();    // stop browser from doing native logic
        window.history.back();
    }
</script>
</head>
<body>
    <a href="#" class="close" onClick="document.location.href='/';">Go back</a>
    <form class="upform" action="/update">
        <div class="fixed">
            <h3><center>Scrum Update Board for {{ dev }}</center></h3>
            <div class="nav">
                <input type="button" class="cancel" value="CANCEL" onclick="document.location.href='/';">
                <h3 class="scrum"><center>Scrum {{ scrum_num }}</center></h3>
                <input type="submit" class="submit" value="SEND">
            </div>
        </div>
        <div class="cont">
            <div class="cont2">
                {% for task in task_list %}
                    <fieldset>
                        <legend><strong>&nbsp;{{ task.1 }} </strong>&nbsp;-&nbsp;&nbsp{{ task.2 }}&nbsp;</legend>
                        &nbsp;Progress: <input type="number" maxlength="3" value="{{ task.3 }}"  class="progress" min="0" max="100" step="10" title="One of: 10,20,30,40,50,60,70,80,90,100" name="progress_{{ task.0 }}"> Today: <input type="checkbox" class="today" name="today_{{ task.0 }}" {% if task.4 %}checked{% endif %}>
Blocker:  <input type="text" class="blocker" maxlength="100" value="{{ task.5 }}" name="blocker_{{ task.0 }}" >
                    </fieldset>
                {% endfor %}
            </div>
        </div>
    </form>
</body>
</html>
'''

#
#  Settings file.
#
DEBUG          = os.environ.get('DEBUG', 'on') == 'on'
SECRET_KEY     = os.environ.get('SECRET_KEY', os.urandom(32))
ALLOWED_HOSTS  = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
ALLOWED_HOSTS  = ['zeuz', 'localhost']
DEFAULT_LOGDIR = '/tmp'
LOGGING_DIR    = os.environ.get('SPRINTVIEW_LOGDIR', DEFAULT_LOGDIR)

settings.configure(
    DEBUG         = DEBUG,
    SECRET_KEY    = SECRET_KEY,
    ALLOWED_HOSTS = ALLOWED_HOSTS,
    ROOT_URLCONF  = __name__,

    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ),
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ],
    CACHES = {
        'default' : {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
        }
    },
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'normal': {
                'format': '%(name)s %(levelname)s %(asctime)s %(process)d [%(message)s] (file: %(pathname)s line: %(lineno)d)'
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            },
           'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            }
        },
        'handlers': {
            'sprintview_file': {
                'class'      : 'logging.handlers.TimedRotatingFileHandler',
                'filename'   :  os.path.join(LOGGING_DIR, 'sprintview.log'),
                'when'       : 'midnight',
                'backupCount': 60,
                'formatter'  : 'normal'
            },
            'console': {
                'class'      : 'logging.StreamHandler',
                'filters'    : ['require_debug_true'],
                'formatter'  : 'normal'
            },
        },
        'loggers': {
            'sprintview_log': {
                'handlers'   : ['sprintview_file', 'console'],
                'level'      : os.getenv('SPRINTVIEW_LOG_LEVEL', 'INFO'),
                'propagate'  : True,
            }
        }
    }
)

from django.core.cache import cache   #  Don't put this before settings file.

#
#  Env vars come likely from a script which allows to pass values
#  into Sprint View's env.
#
DEFAULT_PROJECT     = "test_data"
DEFAULT_PROJECT     = "i5k_workspace_json"
PROJECT_DATA_URL    = 'https://gitlab.com/api/v3/projects/2693506/repository/files'
PROJECT_DATA        = DEFAULT_PROJECT
ISSUES_URL          = 'https://gitlab.com/api/v3/projects/1090162/issues'
SINGLE_ISSUE_URL    = 'https://gitlab.com/i5k_Workspace/workspace_roadmap/issues'
DEFAULT_TOKEN       = 'bBzt3zHyiMczmRXd6adm'   #  Belongs to the app.
SPRINTVIEW_TOKEN    = os.environ.get('SPRINTVIEW_TOKEN', DEFAULT_TOKEN)
DEFAULT_PATH        = './project_data'
DATA_FILE           = os.environ.get('SPRINTVIEW_PATH', DEFAULT_PATH)
DEV_NAMES           = os.environ.get('SPRINTVIEW_DEVELOPERS', '')       # login id/name lookup.
DATA_BACKUP         = '/tmp/project_data.bak'
DEFAULT_SORT_COLUMN = 'dev_sort'
DEFAULT_SORT_ORDER  = 'ascending'
VIEW_EXPIRATION     = 900  # Cached views expire in 15 minutes.
MIN_TOP_HEIGHT      = 22   # Minimum height of top screeen panel (nav).
MAX_BOT_HEIGHT      = 18   # Minimum height of bottom screen (blockers) panel.
MIN_BOT_HEIGHT      = 8    # Minimum height of bottom screen (blockers) panel.
BLK_HEIGHT          = 2    # Height of a blocker item.

#
#  Color shortcuts for get_view().
#
da = '<mark class="dark">'
me = '<mark class="medium">'
li = '<mark class="light">'
dr = '<mark class="dark_red">'
r  = '<mark class="red">'
og = '<mark class="orange">'
td = '<mark class="today">'
em = '</mark>'

FILE = 0   #  Getting data from local file.
URL  = 1   #  Getting data from Gitlab repo.

#
#  Get Agile project data from the GitLab Repo or a file.
#
#  Supports two data origins: file and Gitlab URL.
#
#  Default is file, failing that URL.
#
#  The start script takes care that this is never a problem if
#  we only use a URL habitually.
#
class Data:
    def __init__(self):
        self.data_url   = PROJECT_DATA_URL  #  Url of data store file (GitLab)
        self.data       = {}                #  Project data.
        self.accesstype = FILE              #  Default is local file data.

        self._get_data()
        cache.clear()

    def _get_data(self):

        buf = ''

        if DATA_FILE and os.access(DATA_FILE, os.R_OK):
            #
            #  Get project data from a file.
            #
            with open(DATA_FILE) as f:
                raw_data  = f.read()                # json.
                self.data = json.loads(raw_data)    # dict.

            if not self.data:
                log.error('Data file access provided no data.')
                sys.exit(1)
            log.info('Data source FILE: %s' % DATA_FILE)
        else:
           #
           # Read Repo from GitLab.
           #
            self.accesstype = URL
            headers = {'user-agent':'Mozilla/5.0', 'PRIVATE-TOKEN':SPRINTVIEW_TOKEN}
            payload = {'file_path':PROJECT_DATA, 'ref': 'master'}
            r = requests.get(PROJECT_DATA_URL, headers=headers, params=payload)
            if r.status_code != 200:
                log.error('Failed to open URL %s: code %s' % (PROJECT_DATA_URL, r.status_code))
                sys.exit(1)

            data = json.loads(r.text)                          # dict.
            if 'content' in data and data['content']:
                raw_data  = base64.b64decode(data['content'])  # json.
                self.data = json.loads(raw_data)               # dict.
            else:
                log.error('Empty json file from repo')
                sys.exit(1)
            log.info('Data source URL: %s' % r.url)

        if self.data:
            l = len(raw_data)
            if l >= 1024:
                sz = l / 1024
                log.info("Data store '%s' retrieved - size: %d KB" % (PROJECT_DATA, sz))
            else:
                sz = l
                log.info("'Data store '%s' retrieved - size: %d" % (PROJECT_DATA, sz))
        else:
            log.error('Access method provided no data.')
            sys.exit(1)

    def save(self, proj):
        #
        #  Save the project where it came from.
        #
        buf = json.dumps(proj, indent=4)
        js = buf + '\n'
        if self.accesstype == FILE:
            with open(DATA_FILE, 'w') as f:
                f.write(js)
        elif self.accesstype == URL:
            headers = {'user-agent':'Mozilla/5.0', 'PRIVATE-TOKEN':SPRINTVIEW_TOKEN}
            payload = {'file_path': PROJECT_DATA, 'branch_name': "master", 'commit_message': 'none', 'content': js}
            r = requests.put(PROJECT_DATA_URL, headers=headers, data=payload)
            if r.status_code != 200:
                log.error('Failed to update project date at URL %s: code %s' % (PROJECT_DATA_URL, r.status_code))
                sys.exit(1)
            with open(DATA_BACKUP, 'w') as f:
                f.write(js)


#
#  Container for all sprints in a project.
#
class Project:
    def __init__(self, repo):
        self.repo          = repo     # Project repo.
        self.name          = None     # Project name.
        self.sprint_list   = []       # List of sprints in the project.
        self.issue_list    = []       # List of project issues.
        self.num_sprints   = 0
        self.active_sprint = None
        self.active_scrum  = None
        self.dev_names     = None     # Dictionary to translate developer login id to first name.
        self.dev_ids       = {}       # Dictionary to translate developer name to login id.
        self._make_project()
        self.save_project()

    def _make_project(self):
        #
        # Deserialize repo data from json to Sprint View objects: Project, Sprint, Scrum, etc.
        #
        d = self.repo.data
        if 'name' in d and d['name'] and 'sprint_list' in d:
            self.name = d['name']
        else:
            log.error("No history data found")
            sys.exit(1)

        if DEV_NAMES:
            self.dev_names = ast.literal_eval(DEV_NAMES)
            for dev in self.dev_names:
                name = self.get_dev_name(dev)
                self.dev_ids[name.capitalize()] = dev

        for sprint in d['sprint_list']:
            self.sprint_list.append(Sprint(self, sprint))

        self.num_sprints = len(self.sprint_list)

        if self.num_sprints:
            if self.sprint_list[self.num_sprints - 1].active:
                self.active_sprint = self.sprint_list[self.num_sprints - 1]
                num_scrums = len(self.active_sprint.scrum_list) - 1
                if (num_scrums and self.active_sprint.scrum_list[num_scrums].active):
                    self.active_scrum = self.active_sprint.scrum_list[num_scrums]


    def new_sprint(self):
        #
        #  Start a new sprint.
        #
        #  Initialize new sprint with Scrum 0 and Scrum 1.
        #
        #  Scrum 0 has ScrumTask instances with the previous sprint pending tasks.
        #
        #  Scrum 1 has ScrumTask instances with the previous sprint pending blockers, it's the
        #  Active Scrum, tasks have zero progress, and are open to update.
        #
        assert(not self.active_sprint and not self.active_scrum)
        spr  = {}   #  New sprint dict.
        scr0 = {}   #  New sprint scrum 0 dict.
        scr1 = {}   #  New sprint scrum 1 dict.

        scr1['scrum_task_list'] = []  #  Tasks in this list have only blockers to start with.
        spr['sprint_number']    = self.num_sprints + 1
        spr['sprint_date']      = int(time.time())
        spr['sprint_active']    = True
        spr['sprint_task_list'] = []
        spr['scrum_list']       = []

        #  Scrum 0 -  To hold any carry over tasks.
        scr0['scrum_number'] = 0
        scr0['scrum_active'] = False
        scr0['scrum_task_list'] = []

        if self.num_sprints > 0:
            #
            #  Carry forward unfinished tasks in the previous sprint.
            #
            #  Get lists for Scrum 0 pending tasks and Scrum 1 pending blockers.
            #
            last_sprint = self.sprint_list[self.num_sprints - 1]
            last_scrum  = last_sprint.scrum_list[len(last_sprint.scrum_list) - 1]

            for task in last_sprint.task_list:

                progress, prev_progress, blocker, today = last_sprint.get_task_details(task.task_id, last_sprint, last_scrum.number)

                if progress == 100 or prev_progress == 100:
                    continue

                spr['sprint_task_list'].append(task)   #  This becomes the new sprint task_list.

                tsk  = {}      #  ScrumTask-dict with for the ScrumTask list of Scrum 0.
                tsk2 = {}      #  Task for the task list of Scrum 1 tlist2, with only blockers.

                tsk['task_id'] = task.task_id

                if progress:
                    tsk['progress'] = progress
                else:
                    tsk['progress'] = prev_progress
                tsk['blocker'] = blocker

                if blocker or today:
                    #
                    #  Carry blockers and today tasks forward to Scrum 1.
                    #
                    tsk2['blocker']  = blocker
                    tsk2['task_id']  = task.task_id
                    tsk2['progress'] = progress
                    tsk2['today']    = today
                    tsk2['date']     = time.time()
                    scr1['scrum_task_list'].append(tsk2)

                tsk['today']= False
                tsk['date'] = time.time()
                scr0['scrum_task_list'].append(tsk)
        spr['scrum_list'].append(scr0)

        #  Scrum 1 - Empty of any progress, active scrum, with pending blockers.
        scr1['scrum_number'] = 1
        scr1['scrum_active'] = True
        spr['scrum_list'].append(scr1)
        sprint = Sprint(self, spr)
        self.active_sprint = sprint
        self.active_scrum  = sprint.scrum_list[1]
        self.sprint_list.append(sprint)
        self.num_sprints += 1

    def save_project(self):
        d = {}
        d["name"]        = self.name
        d["repo_url"]    = self.repo.data_url
        d["sprint_list"] = []

        for sprint in self.sprint_list:
            spr = {}
            spr["sprint_number"] = sprint.number
            spr["sprint_date"]   = sprint.date
            spr["sprint_active"] = sprint.active

            spr["sprint_task_list"] = []
            for t in sprint.task_list:
                ti = {}
                ti["task_id"]  = t.task_id
                ti["issue"]    = t.issue
                ti["devel"]    = t.devel
                ti["desc"]     = t.desc
                ti["date"]     = t.date
                spr["sprint_task_list"].append(ti)

            spr["dev_list"] =  sprint.dev_list
            spr["scrum_list"] = []
            for s in sprint.scrum_list:
                si = {}
                si["scrum_number"]    = s.number
                si["scrum_active"]    = s.active
                si["scrum_task_list"] = []
                for t in s.task_list:
                    ti = {}
                    ti["task_id"]  = t.task_id
                    ti["progress"] = t.progress
                    ti["blocker"]  = t.blocker
                    ti["today"]    = t.today
                    ti["date"]     = t.date
                    si["scrum_task_list"].append(ti)
                spr["scrum_list"].append(si)
            d["sprint_list"].append(spr)

        self.repo.save(d)

    def update(self, request):
        #
        #  Update a developer's tasks in the current scrum.
        #
        assert(self.is_scrum_active())

        #
        #  Get the set of task_ids in the update.
        #
        id_set = set()
        for key in request.GET:
            if key.startswith("progress_") or key.startswith("today_") or key.startswith("blocker_"):
                id_set.add(key.split('_')[1])
            else:
                log.warn('STRANGE KEY: %s' %  key)

        #
        #  if the task particulars have changed, update them.
        #
        refresh = False    #  Whether to refresh the view or not.

        for task_id in id_set:
            t = {}
            t["task_id"]  = task_id
            key = "progress_" + task_id
            if key in request.GET:
                t["progress"] = request.GET[key]
            else:
                t["progress"] = 0
            key = "blocker_" + task_id
            if key in request.GET:
                t["blocker"]  = request.GET[key]
            else:
                t["blocker"] = ''
            key = "today_" + task_id
            if key in request.GET:
                t["today"] = True if request.GET[key] else False
            else:
                t["today"] = False
            t["date"] = time.time()

            progress, dontcare, blocker, today = self.active_sprint.get_task_details(task_id, self.active_sprint, self.active_scrum.number)

            if t["progress"] != progress or t["today"] != today or t["blocker"] != blocker:
                #
                #  This task changed, update it.
                #
                refresh = True
                #
                #  Is there a ScrumTask for this task already, from a previous update?
                #
                tsk = self.active_scrum.get_task(task_id)
                if  tsk:
                    tsk.progress = t["progress"]
                    tsk.today    = t["today"]
                    tsk.blocker  = t["blocker"]
                    tsk.date     = t["date"]
                else:
                    #
                    #  Create new ScrumTask.
                    #
                    self.active_scrum.add_task(t)   #  Add to scrum task_list.

        if refresh:
            self.save_project()

        return refresh

    def is_scrum_active(self):
        return bool(self.active_sprint and self.active_scrum)

    def is_sprint_active(self):
        return bool(self.active_sprint)

    def project_edit(self, request):
        #
        #  CLI command processing.  Commands format:
        #
        #     cmd:val
        #
        #  or just
        #
        #     cmd
        #
        changed = False
        if 'cli_text' in request and request['cli_text']:
            cmd_list = request['cli_text'].split(';')

            for cmd in cmd_list:
                l = cmd.split(':')
                if not l:
                    return False
                key = l[0].strip()
                if not key:
                    return False
                if len(l) == 2:
                    val = l[1].strip()
                    if not val:
                        return False
                log.info('project_edit: running command: %s' % cmd)

                if key.startswith('-'):
                    #
                    #  Delete task.
                    #
                    changed = self.active_sprint.delete_task(cmd[1:])
                elif key == 'scrm':
                    #
                    #  Delete a scrum.
                    #
                    i = 0
                    if self.is_sprint_active():
                        for scr in self.active_sprint.scrum_list:
                            if str(scr.number) == val:
                                self.active_sprint.scrum_list.pop(i)
                                changed = True
                            i =+ 1
                        #
                        #  Renumber scrums.
                        #
                        i = 0
                        for scr in self.active_sprint.scrum_list:
                            scr.number = i
                            i += 1

                elif key == 'sprm':
                    #
                    #  Delete a sprint.
                    #
                    i = 0
                    for spr in self.sprint_list:
                        if str(spr.number) == val:
                            self.sprint_list.pop(i)
                            self.num_sprints -= 1
                            if spr == self.active_sprint:
                                self.active_sprint = None
                                self.active_scrum = None
                            changed = True
                        i += 1
                    #
                    #  Renumber sprints.
                    #
                    i = 1
                    for spr in self.sprint_list:
                        spr.number = i
                        i += 1

                elif key == 'scop':
                    #
                    #  Re-open last scrum.
                    #
                    if self.is_sprint_active():
                        if not self.active_scrum:
                            num = len(self.active_sprint.scrum_list)
                            if num > 1:
                                scr = self.active_sprint.scrum_list[num - 1]
                                scr.active = True
                                self.active_scrum = scr
                                changed = True
                elif key == 'spop':
                    #
                    #  Re-open last sprint.
                    #
                    if not self.is_sprint_active():
                        if self.num_sprints > 0:
                            spr = self.sprint_list[self.num_sprints - 1]
                            spr.active = True
                            self.active_sprint = spr
                            changed = True

            return changed

    def get_dev_name(self, logid):
        #
        #  Returns a developer's name given its login id, if it exists.
        #
        if self.dev_names:
            if logid in self.dev_names:
                return self.dev_names[logid].capitalize()
        return logid

    def get_dev_id(self, name):
        #
        #  Given a developer name, get its Gitlab login id, if it exists
        #
        if name in self.dev_ids:
            return self.dev_ids[name]
        elif name.lower() in self.dev_ids:
            return self.dev_ids[name.lower()]
        elif name.capitalize() in self.dev_ids:
            return self.dev_ids[name.capitalize()]
        else:
            return name


#
#  Container for all scrums in a sprint.
#
class Sprint:
    def __init__(self, project, sprint):
        self.project    = project                  #  Project the sprint belongs to.
        self.number     = sprint['sprint_number']
        self.date       = sprint['sprint_date']
        self.task_list  = []                       #  Sprint Task list.
        self.scrum_list = []                       #  Scrums in the sprint.
        self.active     = sprint['sprint_active']
        self.dev_list   = []                       #  List of developers in this sprint.

        for task in sprint['sprint_task_list']:
            tsk = SprintTask(self, task)
            self.task_list.append(tsk)

        self.get_dev_list()

        for scrum in sprint['scrum_list']:
            scr = Scrum(self, scrum)
            self.scrum_list.append(scr)

    def get_issue(self, issue_id):
        #
        #  Get issue data.
        #
        headers = {'user-agent':'Mozilla/5.0', 'PRIVATE-TOKEN':SPRINTVIEW_TOKEN}
        payload = {'iid': issue_id}
        r = requests.get(ISSUES_URL, headers=headers, params=payload)
        if r.status_code != 200:
            log.error('Failed to open URL %s: code %s' % (ISSUES_URL, r.status_code))
            sys.exit(1)
        l = json.loads(r.text)
        return l[0]

    def get_task(self, task_id):
        #
        #  Get a sprint task by id.
        #
        for t in self.task_list:
            if task_id == t.task_id:
                return t
        return False

    def task_exists(self, task_id):
        if self.get_task(task_id):
            return True
        return False

    def new_scrum(self):
        #
        #  Start a new scrum.
        #
        num = len(self.scrum_list)
        scr = {}
        scr['scrum_number'] = num
        scr['scrum_active'] = True
        scr['scrum_task_list'] = []
        last_scrum = self.scrum_list[len(self.scrum_list) - 1]
        for task in self.project.active_sprint.task_list:
            for tsk in last_scrum.task_list:
                if tsk.task_id == task.task_id:
                    if tsk.blocker or tsk.today:
                        #
                        #  Carry blockers and today's tasks forward.
                        #
                        t             = {}
                        t["task_id"]  = task.task_id
                        t['today']    = tsk.today
                        t['progress'] = tsk.progress
                        t['blocker']  = tsk.blocker
                        t['date']     = time.time()
                        scr['scrum_task_list'].append(t)

        scrum = Scrum(self.project.active_sprint, scr)
        self.project.active_sprint.scrum_list.append(scrum)
        self.project.active_scrum = scrum

    def get_dev_tasks(self, name):
        #
        #  Get the tasks assigned to a developer, by developer's name.
        #
        #  Returns a list of tuples like this: (issue, description, progress, today, blocker)
        #
        assert(self.project.is_scrum_active())
        dev = self.project.get_dev_id(name)
        l = []
        for task in self.project.active_sprint.task_list:
            if task.devel == dev:
                progress, prev_progress, blocker, today = self.get_task_details(task.task_id, self.project.active_sprint, self.project.active_scrum.number)
                if not progress:
                    progress = prev_progress
                l.append((task.task_id, task.issue, task.desc, progress, today, blocker))
        return l

    def close(self):
        #
        #  Close the current sprint.
        #
        assert(self.active)
        self.active = False
        if self.project.active_scrum:
            if self.project.active_scrum.active:
                self.project.active_scrum.close()
            self.project.active_sprint = None

    def add_tasks(self, request):
        #
        #  Add a new task to the current sprint.
        #  request has the GET request reply from
        #  Gitlab with the issue data.
        #
        assert(self.project.active_sprint.active)
        changed = False
        if 'issue_list' in request and request['issue_list']:
            for task in request['issue_list'].split(','):
                task = task.strip()
                l = task.split(':')
                if len(l) == 2:
                    #
                    #  The assignee is given.
                    #
                    num  = l[1]
                    name = l[0]
                    dev  = self.project.get_dev_id(name)
                    task_id = dev + ':' + num
                    d = self.get_issue(num)
                else:
                    #
                    #  Get assignee from Gitlab.
                    #
                    assert(task.isdigit())
                    d = self.get_issue(task)
                    if d['assignee'] and d['assignee']['username']:
                        dev = d['assignee']['username']
                    elif d['author'] and d['author']['username']:
                        dev = d['author']['username']
                    else:
                        log.error('No developer assigned to task %s' % task)
                        sys.exit(1)
                    task_id = dev + ':' + task

                if self.project.active_sprint.task_exists(task_id):
                    log.warn('Task %s already exist' % task_id)
                    continue

                ti            =  {}
                ti["task_id"] = task_id
                ti["issue"]   = d['iid']
                ti["devel"]   = dev
                ti["desc"]    = d['title']
                ti["date"]    = time.time()
                tsk = SprintTask(self, ti)
                self.project.active_sprint.task_list.append(tsk)
                self.project.active_sprint.get_dev_list()
                changed = True

        if changed:
            self.project.save_project()

        return changed

    def delete_task(self, task_id):
        #
        #  Task_id can be just an issue number or a proper task_id.
        #
        #  If only issue number, delete all tasks with that issue number.
        #
        #  ScrumTasks for the delete task remain in place, invisibly. If the task
        #  were added again, its previous status would show again.
        #
        dev     = ''
        changed = False
        task_id = task_id.strip()
        dlist   = []
        field = task_id.split(':')
        num_fields = len(field)
        if num_fields == 2:
            #
            #  Command carries a whole task_id, with developer name.
            #
            name = field[0].strip()

            dev  = self.project.get_dev_id(name)
            num  = field[1].strip()
            task_id = dev + ':' + num
            dlist.append(task_id)
        elif num_fields == 1:
            #
            #  Command carries only issue number.
            #
            num = task_id
            assert(num.isdigit())
            for t in self.task_list:
                if t.issue == int(num):
                    dlist.append(t.task_id)
        for tid in dlist:
            i = 0
            for t in self.task_list:

                if tid == t.task_id:
                    dt = self.task_list.pop(i)
                    changed = True
                    break
                i += 1

        return changed

    def get_dev_list(self):
        devs = set()
        for task in self.task_list:
            devs.add(task.devel)
        self.dev_list = list(devs)

    def get_task_details(self, task_id, sprint, scrum_num):
        #
        #  Returns the current progress, previous progress,
        #  blocker, and today of a task for a given scrum.
        #
        assert (scrum_num > 0)
        progress = 0
        prev_progress = 0
        blocker = ''
        today = False
        for scr in sprint.scrum_list:
            for t in scr.task_list:
                if t.task_id == task_id:
                    if scr.number == scrum_num:
                        progress = t.progress
                        blocker  = t.blocker
                        today    = t.today
                    else:
                        prev_progress = t.progress
                    continue
            if scr.number == scrum_num:
                break

        return (int(progress), int(prev_progress), blocker, today)


#
#  Container for all developers' reports in a scrum.
#
class Scrum:
    def __init__(self, sprint, scrum):
        self.sprint    = sprint    #  Sprint object.
        self.task_list = []        #  Scrum task list.
        self.active = scrum['scrum_active']
        self.number = scrum['scrum_number']

        for tsk in scrum['scrum_task_list']:
            task = ScrumTask(self, tsk)
            self.task_list.append(task)

    def get_task(self, task_id):
        for t in self.task_list:
            if task_id == t.task_id:
                return t
        return False

    def add_task(self, tsk):
        task = ScrumTask(self, tsk)
        self.task_list.append(task)

    def close(self):
        assert (self.active)
        self.active = False
        self.sprint.project.active_scrum = None

#
#  Container for a sprint task.
#
class SprintTask:
    def __init__(self, sprint, task):
        self.sprint   = sprint
        if type(task) == dict:
            self.task_id  = task['task_id']
            self.devel    = task['devel']
            self.issue    = task['issue']
            self.desc     = task['desc']
            self.date     = task['date']      # Datetime of creation or latest update.
        else:
            self.task_id  = task.task_id
            self.devel    = task.devel
            self.issue    = task.issue
            self.desc     = task.desc
            self.date     = task.date      # Datetime of creation or latest update.

    def make_issue_link(self):
        return('<a href="%s/%s" target="blank">%s</a>' % (SINGLE_ISSUE_URL, self.issue, self.issue))


#
#  Container for the scrum task progress report.
#
class ScrumTask:
    def __init__(self, scrum, task):
        self.scrum    = scrum
        self.task_id  = task['task_id']
        self.progress = task['progress']
        self.blocker  = task['blocker']
        self.today    = task['today']    # Boolean, true if task is today's work.
        self.date     = task['date']     # Datetime of submission.


#
#  Cache view - To cache views already generated.
#
class CacheView:
    def __init__(self, sprint_num, scrum_num, sort_column, sort_order, task_list, blocker_list):
        self.sprint_num   = sprint_num
        self.scrum_num    = scrum_num,
        self.sort_column  = sort_column
        self.sort_order   = sort_order
        self.task_list    = task_list
        self.blocker_list = blocker_list

    def same_sort_column(self, view):
        if view.sort_column == self.sort_column:
            return True
        return False

    def same_sort_order(self, view):
        if view.sort_order == self.sort_order:
            return True
        return False

#
#  Display data container.
#
#  A view is the collection of data to display the sprint in a particular manner.
#
#  A view is defined by the tuple:
#
#      sprint number,
#      scrum number,
#      sort column,
#      sort order,
#      task list,
#      blocker list.
#
class View:
    def __init__(self, project):
        self.project        = project              # Pointer to project.
        self.cur_sprint_num = 0                    # Current sprint number.
        self.cur_scrum_num  = 0                    # Current scrum number.
        self.cur_sprint     = None                 # Current sprint object.
        self.cur_scrum      = None                 # Current scrum object.
        self.num_sprints    = 0                    # Number of sprints in the project.
        self.num_scrums     = 0                    # Number of scrums in current sprint.
        self.sort_column    = DEFAULT_SORT_COLUMN  # Sort view by this table column.
        self.sort_order     = DEFAULT_SORT_ORDER   # 'ascending' or 'descending.'

        self._init_view()

    def _init_view(self):
        self.num_sprints = len(self.project.sprint_list)
        if self.num_sprints:
            self.cur_sprint_num = self.num_sprints
            self.cur_sprint     = self.project.sprint_list[self.cur_sprint_num - 1]
            self.num_scrums     = len(self.cur_sprint.scrum_list) - 1
            self.cur_scrum_num  = self.num_scrums
            self.cur_scrum      = self.cur_sprint.scrum_list[self.cur_scrum_num]
        else:
            self.cur_sprint_num = 0
            self.cur_sprint     = None
            self.num_scrums     = 0
            self.cur_scrum_num  = 0
            self.cur_scrum      = None

    def _make_cache_tag(self):
        return str(self.cur_sprint_num) + ':' + str(self.cur_scrum_num) + ':' + self.sort_column + ':' + self.sort_order

    def get_view(self):
        #
        #  Main function to gather all screen data ready for rendering.
        #
        if not self.project.num_sprints:
            return (([], [], 'dev_sort', 'ascending'))

        sprint_num = self.cur_sprint_num
        scrum_num  = self.cur_scrum_num

        sprint = self.cur_sprint
        scrum  = self.cur_scrum

        prev_view = cache.get(self._make_cache_tag())

        if not prev_view:
            #
            # Generate the view for the first time.
            #
            task_list   = []
            blocker_list = []

            for t in sprint.task_list:
                #
                #   For each sprint task:
                #
                #      Check from Scrum 0 to the requested scrum for
                #      progress, blockers, and today status.  And process
                #      text for display.
                #
                gain          = 0
                progress      = 0
                prev_progress = 0
                blocker       = ''

                progress, prev_progress, blocker, today = sprint.get_task_details(t.task_id, sprint, scrum_num)

                if blocker:
                    name = proj.get_dev_name(t.devel)
                    blk = name[:10] + ': ' + t.make_issue_link() + ': ' + t.desc + ': ' + blocker
                    blocker_list.append(blk)

                if not progress and not prev_progress:
                    #
                    #  There are no ScrumTasks for this task.
                    #
                    p = da + '[0]' + em
                    if blocker:
                        p += r + 'Blocked' + em

                    #
                    #  There is no progress for this feature so far.
                    #
                    if today:
                        desc = td + t.desc[:90] + em
                    else:
                        desc = t.desc[:90]

                    name = proj.get_dev_name(t.devel)
                    task_list.append((name[:10], t.make_issue_link(), desc, p))
                    continue

                #
                #  Add the progress for this feature so far.
                #  And color the status strings.
                #
                prev_progress_str = ''
                gain_str          = ''

                if progress:
                    gain = progress - prev_progress
                    if gain:
                        gain_str      = str(gain)
                        gain_str_len  = len(gain_str)
                    if gain < 0:
                        prev_progress = progress
                        gain_str = og + '&lt;' + ('-' * ((abs(gain) / 2) - gain_str_len - 1) + gain_str) + '&nbsp;' + em
                    elif gain > 0:
                        total_str = da + '[' +  str(progress) + ']' + em
                        gain_str  = li + (('&nbsp;' * ((gain / 2) - gain_str_len)) + gain_str) + em + total_str

                if prev_progress:
                    prev_progress_str     = str(prev_progress)
                    prev_progress_str_len = len(prev_progress_str)
                    if gain > 0:
                        prev_progress_str = me + ('&nbsp;' * ((prev_progress / 2) - prev_progress_str_len) + prev_progress_str) + em
                    else:
                        total_str = da + '[' +  str(prev_progress) + ']' + em
                        prev_progress_str = me +  ('&nbsp;' * ((prev_progress / 2) - prev_progress_str_len)  + prev_progress_str) + em + total_str

                p = prev_progress_str + gain_str

                if not p:
                    p = da + '[0]' + em

                if blocker:
                    p = p + r + 'Blocked' + em

                if today:
                    desc = td + t.desc[:90] + em  #  Highlights today's tasks.
                else:
                    desc = t.desc[:90]

                name = proj.get_dev_name(t.devel)
                task_list.append((name[:10], t.make_issue_link(), desc, p))
            #
            #  Color the blockers.
            #
            blocker_list = [ dr + blk + em for blk in blocker_list]
        else:
            #
            #  View in cache, retrieve task and blocker lists.
            #
            task_list = prev_view.task_list
            blocker_list = prev_view.blocker_list

        if not prev_view:
            #
            #  Sort task list by sort column and sort order.
            #
            reverse_sort = True if self.sort_order == "descending" else False

            if self.sort_column == 'dev_sort':
                task_list.sort(key=lambda tup: tup[0], reverse=reverse_sort)
            elif self.sort_column == 'issue_sort':
                task_list.sort(key=lambda tup: tup[1], reverse=reverse_sort)
            elif self.sort_column == 'desc_sort':
                task_list.sort(key=lambda tup: tup[2], reverse=reverse_sort)
            elif self.sort_column == 'status_sort':
                task_list.sort(key=lambda tup: int(tup[3].split('[')[1].split(']')[0]), reverse=reverse_sort)

            #
            #  Cache this view.
            #
            prev_view = CacheView(self.cur_sprint_num, self.cur_scrum_num, self.sort_column, self.sort_order, task_list, blocker_list)
            cache.set(self._make_cache_tag(), prev_view, VIEW_EXPIRATION)

        return ((task_list, blocker_list, self.sort_column, self.sort_order))

    #
    #  Setter/Getter functions.
    #
    def set_next_sprint(self):
        self.cur_sprint_num += 1
        self.cur_sprint_num %= self.num_sprints
        if self.cur_sprint_num == 0:
            self.cur_sprint_num = self.num_sprints
        self.cur_sprint      = self.project.sprint_list[self.cur_sprint_num - 1]
        self.num_scrums      = len(self.cur_sprint.scrum_list) - 1
        self.cur_scrum_num   = self.num_scrums
        self.cur_scrum       = self.cur_sprint.scrum_list[self.cur_scrum_num]

    def set_prev_sprint(self):
        self.cur_sprint_num -= 1
        self.cur_sprint_num %= self.num_sprints
        if self.cur_sprint_num == 0:
            self.cur_sprint_num = self.num_sprints
        self.cur_sprint      = self.project.sprint_list[self.cur_sprint_num - 1]
        self.num_scrums      = len(self.cur_sprint.scrum_list) - 1
        self.cur_scrum_num   = self.num_scrums
        self.cur_scrum       = self.cur_sprint.scrum_list[self.cur_scrum_num]

    def set_next_scrum(self):
        self.cur_scrum_num += 1
        self.cur_scrum_num %= self.num_scrums
        if self.cur_scrum_num == 0:
            self.cur_scrum_num = self.num_scrums
        self.cur_scrum = self.cur_sprint.scrum_list[self.cur_scrum_num]

    def set_prev_scrum(self):
        self.cur_scrum_num -= 1
        self.cur_scrum_num %= self.num_scrums
        if self.cur_scrum_num == 0:
            self.cur_scrum_num = self.num_scrums
        self.cur_scrum = self.cur_sprint.scrum_list[self.cur_scrum_num]

    def set_sort_column(self, sort_column):
        if sort_column == self.sort_column:
            self.sort_order = 'descending' if self.sort_order == 'ascending' else 'ascending'
        else:
            self.sort_order = 'ascending'
            self.sort_column = sort_column

    def set_last(self):
        self._init_view()

    def get_num_sprints(self):
        return(self.num_sprints)

    def get_num_scrums(self):
        return(self.num_scrums)

    def get_sprint_num(self):
        return(self.cur_sprint_num)

    def get_sprint_date(self):
        if not self.cur_sprint:
            return ''
        else:
            if type(self.cur_sprint.date) == int:
                year_now  = datetime.datetime.today().strftime('%Y')
                year_then = datetime.datetime.fromtimestamp(self.cur_sprint.date).strftime('%Y')
                if year_now == year_then:
                    return datetime.datetime.fromtimestamp(self.cur_sprint.date).strftime('%b %-d')
                else:
                    return datetime.datetime.fromtimestamp(self.cur_sprint.date).strftime('%b %-d %y')

            else:
                return(self.cur_sprint.date)

    def get_scrum_num(self):
        return(self.cur_scrum_num)

    def get_num_tasks(self):
        if not self.cur_sprint:
            return 0
        else:
            return(len(self.cur_sprint.task_list))


def init():
    global log

    if not os.access(LOGGING_DIR, os.W_OK):
        log.error('Can\'t write to logging dir: %s' % LOGGING_DIR)
        sys.exit(1)

    #
    #  Create file rotating logger.
    #
    log = logging.getLogger('sprintview_log')
    log.info('Sprint View Starting.  Project file: %s' % PROJECT_DATA)


def index(request):
    #
    #  All URLs come here.
    #
    global proj
    global view
    global inited

    re_load = False

    if request.method == "GET":

        param = request.path.split('/')[1]

        if inited == False:
            #
            #  First request.
            #
            init()
            data   = Data()               #  Get Repo data as a dictionary.
            proj   = Project(data)        #  Global. Process and store repo data.
            view   = View(proj)           #  Global. Initialize first page to view.
            inited = True

        if request.path == '/':
            pass    #  First request and Go back buttons
        #
        #  Move view to next/prev sprint/scrum, or other.
        #
        elif request.path == '/prev_scrum':
            view.set_prev_scrum()
        elif request.path == '/next_scrum':
            view.set_next_scrum()
        elif request.path == '/prev_sprint':
            view.set_prev_sprint()
        elif request.path == '/next_sprint':
            view.set_next_sprint()
        elif request.path == '/last':
            view.set_last()
        elif request.path.endswith('sort'):
            sort_column = param
            view.set_sort_column(sort_column)
        elif request.path == '/reload':
            re_load = True
        elif request.path == '/update':
            re_load = proj.update(request)
        elif request.path.startswith('/devel_'):
            assert proj.active_sprint
            dev  = param.split('_')[1]
            task_list = proj.active_sprint.get_dev_tasks(dev)
            l = len(task_list)
            #  Distance between developers tasks on the update board.
            if l == 2:
                interfield = 30
            elif l == 3:
                interfield = 20
            elif l == 4:
                interfield = 10
            elif l == 5:
                interfield = 5
            else:
                interfield = 0
            name = proj.get_dev_name(dev)
            t = Template(update_page)
            c = Context({'task_list': task_list, 'dev': name, 'scrum_num': proj.active_scrum.number, 'interfield': interfield})
            return  HttpResponse(t.render(c))
        elif request.path == '/close_scrum':
            if proj.active_scrum:
                proj.active_scrum.close()
                proj.save_project()
                re_load = True
        elif request.path == '/close_sprint':
            if proj.active_sprint:
                proj.active_sprint.close()
                proj.save_project()
                re_load = True
        elif request.path == '/new_scrum':
            if proj.active_sprint:
                proj.active_sprint.new_scrum()
                proj.save_project()
                re_load = True
        elif request.path == '/new_sprint':
            if not proj.active_sprint:
                proj.new_sprint()
                proj.save_project()
                re_load = True
        elif request.path == '/task_add':
            re_load = proj.active_sprint.add_tasks(request.GET)
        elif request.path == '/cli':
            re_load = proj.project_edit(request.GET)
            if re_load:
                proj.save_project()
        else:
            return HttpResponse('Invalid request path, sorry.')

        if re_load:
            data = Data()          #  Get Repo data.
            proj = Project(data)   #  Global. Process and store repo data.
            view = View(proj)      #  Global. Initialize first page to view.

        task_list, blocker_list, sort_column, sort_order = view.get_view()   # Generate view data.

        if blocker_list:
            blocker_label = 'Blockers:'
            nblk = len(blocker_list)
            bot_height = MIN_BOT_HEIGHT + (BLK_HEIGHT * nblk)    #  Height of bot_frame (blockers) screen frame.
            if bot_height > MAX_BOT_HEIGHT:
                bot_height = MAX_BOT_HEIGHT
        else:
            blocker_label = 'Blockers: None'
            bot_height = MIN_BOT_HEIGHT

    else:
        return HttpResponse('Invalid request method (%s). Only GET requests accepted, sorry.' % request.method)

    dev_list = []
    if proj.active_sprint and proj.active_scrum:
        for dev in proj.active_sprint.dev_list:
             dev_list.append(proj.get_dev_name(dev))

    scrum_active = proj.is_scrum_active()

    scrum_on = True if proj.active_scrum else False
    sprint_on = True if proj.active_sprint else False

    mid_height = 100.5 - MIN_TOP_HEIGHT - bot_height   #  Height of middle screen frame.
    #
    # Render view.
    #
    t = Template(page)
    c = Context({'task_list'   : task_list,
                 'blk_list'    : blocker_list,
                 'dev_list'    : dev_list,
                 'blk_label'   : blocker_label,
                 'num_sprints' : view.get_num_sprints(),
                 'num_scrums'  : view.get_num_scrums(),
                 'num_tasks'   : view.get_num_tasks(),
                 'sprint_num'  : view.get_sprint_num(),
                 'sprint_date' : view.get_sprint_date(),
                 'scrum_num'   : view.get_scrum_num(),
                 'sort_column' : sort_column,
                 'sort_order'  : sort_order,
                 'scrum_on'    : scrum_on,
                 'sprint_on'   : sprint_on,
                 'scrum_active': scrum_active,
                 'mid_height'  : mid_height,
                 'bot_height'  : bot_height
    })
    return  HttpResponse(t.render(c))

urlpatterns = (
    url(r'^$', index),
    url(r'prev_sprint', index),
    url(r'next_sprint', index),
    url(r'prev_scrum', index),
    url(r'next_scrum', index),
    url(r'last', index),
    url(r'reload', index),
    url(r'dev_sort', index),
    url(r'issue_sort', index),
    url(r'desc_sort', index),
    url(r'status_sort', index),
    url(r'close_scrum', index),
    url(r'close_sprint', index),
    url(r'new_scrum', index),
    url(r'new_sprint', index),
    url(r'devel', index),
    url(r'update', index),
    url(r'task_add', index),
    url(r'task_delete', index),
    url(r'cli', index),
)

application = get_wsgi_application()

if __name__ == "__main__":

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
