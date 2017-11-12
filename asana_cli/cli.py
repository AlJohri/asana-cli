import os
import sys
import json
import click
import logging
import requests

logger = logging.getLogger(__name__)

# TODO: add this to a --verbose parameter.
#       global verbose parameter is hard in Click
#       see https://github.com/pallets/click/issues/108
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('requests').setLevel(logging.WARNING)
# logging.getLogger('urllib3').setLevel(logging.WARNING)


try:
    ASANA_TOKEN = os.environ['ASANA_TOKEN']
except KeyError:
    print("environment variable ASANA_TOKEN is not set", file=sys.stderr)
    sys.exit(1)

s = requests.Session()
s.headers = {"Authorization": f"Bearer {ASANA_TOKEN}"}

def parse_asana_error_response(response):
    try:
        data = response.json()
        error = str(data)
        if data.get('errors') and len(data['errors']) == 1:
            try:
                message = data['errors'][0]['message']
                help_text = data['errors'][0]['help']
                error = f"{message}. {help_text}"
            except (IndexError, KeyError,) as e:
                pass
    except ValueError:
        error = response.text
    return error

def response_to_json(response):
    if response.status_code != 200:
        error = parse_asana_error_response(response)
        print(error, file=sys.stderr)
        sys.exit(1)
    else:
        data = response.json()
        return data

def get(url):
    logger.debug(f"getting url {url}")
    response = s.get(url)
    response_json = response_to_json(response)
    data = response_json['data']
    if type(data) is dict:
        count = 1
    else:
        count = len(data)
    has_next_page = True if response_json.get('next_page') else False
    logger.debug(f"got {count} records for {url}. has next page?: {has_next_page}")
    return response_json

def get_json(url):
    response_json = get(url)
    return response_json['data']

def get_paginated_json(url):
    items = []
    # TODO: this can be written better using urllib.parse
    if "?" in url:
        url += "&limit=100"
    else:
        url += "?limit=100"
    while True:
        response_json = get(url)
        items += response_json['data']
        if not response_json.get('next_page'): break
        url = response_json['next_page']['uri']
    return items

def get_item(item_type, items, name):
    try:
        return [x for x in items if x['name'] == name][0]
    except IndexError:
        print(f"unable to find {item_type} {name}", file=sys.stderr)
        sys.exit(1)

def get_workspaces():
    profile = get_json(f"https://app.asana.com/api/1.0/users/me")
    workspaces = profile['workspaces']
    return workspaces

def get_workspace(name):
    workspaces = get_workspaces()
    return get_item("workspace", workspaces, name)

def get_projects(workspace):
    workspace_id = workspace['id']
    projects = get_paginated_json(f"https://app.asana.com/api/1.0/workspaces/{workspace_id}/projects?opt_fields=name,layout")
    return projects

def get_project(name, workspace):
    projects = get_projects(workspace)
    return get_item("project", projects, name)

def get_sections(project):
    project_id = project['id']
    sections = get_paginated_json(f"https://app.asana.com/api/1.0/projects/{project_id}/sections")
    return sections

def get_section(name, project):
    sections = get_sections(project)
    return get_item("section", sections, name)

def get_tasks(project, section=None):
    if section:
        section_id = section['id']
        tasks = get_paginated_json(f"https://app.asana.com/api/1.0/sections/{section_id}/tasks?opt_fields=completed")
    else:
        project_id = project['id']
        tasks = get_paginated_json(f"https://app.asana.com/api/1.0/projects/{project_id}/tasks?opt_expand=completed,memberships")
    return tasks

@click.group()
def main():
    """
    \b
    Examples:

    \b
    asana list workspaces
    asana list projects --workspace="Personal Projects"
    asana list tasks --workspace="Personal Projects" --project="Test"
    asana list sections --workspace="Personal Projects" --project="Test"
    asana list tasks --workspace="Personal Projects" --project="Test" --section="Column 1"

    \b
    asana delete tasks --workspace="Personal Projects" --project="Test" --section="Column 1"

    \b
    asana mark tasks --workspace="Personal Projects" --project="Test" --section="Column 1" --completed
    asana mark tasks --workspace="Personal Projects" --project="Test" --section="Column 1" --not-completed

    \b
    asana move tasks --workspace="Personal Projects" --from-project="Test" --from-section="Column 1" --to-section="Column 2"
    """
    pass

# ---------------------------------
# list

@main.group(name='list')
def list_():
    pass

@list_.command(name='workspaces')
def list_workspaces():
    workspaces = get_workspaces()
    for workspace in workspaces:
        print(json.dumps(workspace))

@list_.command(name='projects')
@click.option('--workspace', required=True)
def list_projects(workspace):
    workspace_obj = get_workspace(workspace)
    projects = get_projects(workspace_obj)
    for project in projects:
        print(json.dumps(project))

@list_.command(name='sections')
@click.option('--workspace', required=True)
@click.option('--project', required=True)
def list_sections(workspace, project):
    workspace_obj = get_workspace(workspace)
    project_obj = get_project(project, workspace=workspace_obj)
    sections = get_sections(project_obj)
    for section in sections:
        print(json.dumps(section))

@list_.command(name='tasks')
@click.option('--workspace', required=True)
@click.option('--project', required=True)
@click.option('--section')
def list_tasks(workspace, project, section):
    workspace_obj = get_workspace(workspace)
    project_obj = get_project(project, workspace=workspace_obj)
    section_obj = get_section(section, project=project_obj) if section else None
    tasks = get_tasks(project_obj, section=section_obj)
    for task in tasks:
        print(json.dumps(task))

# ---------------------------------
# move

@main.group()
def move():
    pass

def move_tasks_inner(source_project, source_section, target_project, target_section):
    """
    move tasks from source to target
    """
    source_project_id, source_project_name = source_project['id'], source_project['name']
    source_section_id, source_section_name = source_section['id'], source_section['name']
    target_project_id, target_project_name = target_project['id'], target_project['name']
    target_section_id, target_section_name = target_section['id'], target_section['name']

    source_tasks = get_paginated_json(f"https://app.asana.com/api/1.0/sections/{source_section_id}/tasks")

    if len(source_tasks) == 0:
        print(f"no tasks to move in section {source_section_name} of project {source_project_name}")

    for task in source_tasks:
        task_id = task['id']
        if source_project_id == target_project_id:
            print(f"moving task {task_id} from {source_section_name} to {target_section_name} "
                  f"within project {target_project_name}", end="...")
        else:
            print(f"moving task {task_id} from {source_section_name} in {source_project_name} "
                                          f"to {target_section_name} in {target_project_name}", end="...")
        response = s.post(f"https://app.asana.com/api/1.0/tasks/{task_id}/addProject", data={
            "project": target_project_id, "section": target_section_id})
        if response.status_code != 200:
            print(f"failed")
            error = parse_asana_error_response(response)
            print(error, file=sys.stderr)
            sys.exit(1)
        else:
            print(f"success!")

@move.command(name='tasks')
@click.option('--workspace', required=True)
@click.option('--from-project', required=True)
@click.option('--from-section', required=True)
@click.option('--to-project')
@click.option('--to-section', required=True)
def move_tasks(workspace, from_project, from_section, to_project, to_section):
    workspace_obj = get_workspace(workspace)
    from_project_obj = get_project(from_project, workspace=workspace_obj)
    from_section_obj = get_section(from_section, project=from_project_obj)
    to_project_obj = get_project(to_project, workspace=workspace_obj) if to_project else from_project_obj
    to_section_obj = get_section(to_section, project=to_project_obj)

    move_tasks_inner(from_project_obj, from_section_obj, to_project_obj, to_section_obj)

# ---------------------------------
# delete

@main.group()
def delete():
    pass

@delete.command(name='tasks')
@click.option('--workspace', required=True)
@click.option('--project', required=True)
@click.option('--section', required=True)
def delete_tasks(workspace, project, section):
    workspace_obj = get_workspace(workspace)
    project_obj = get_project(project, workspace=workspace_obj)
    section_obj = get_section(section, project=project_obj)
    tasks = get_tasks(project_obj, section=section_obj)
    for task in tasks:
        task_id = task['id']
        print(f"deleting {task_id}", end="...")
        response = s.delete(f"https://app.asana.com/api/1.0/tasks/{task_id}")
        if response.status_code != 200:
            print(f"failed")
            error = parse_asana_error_response(response)
            print(error, file=sys.stderr)
            sys.exit(1)
        else:
            print(f"success")

# ---------------------------------
# mark

@main.group()
def mark():
    pass

@mark.command(name='tasks')
@click.option('--workspace', required=True)
@click.option('--project', required=True)
@click.option('--section', required=True)
@click.option('--completed/--not-completed', default=True)
def mark_tasks(workspace, project, section, completed):
    workspace_obj = get_workspace(workspace)
    project_obj = get_project(project, workspace=workspace_obj)
    section_obj = get_section(section, project=project_obj)
    tasks = get_tasks(project_obj, section=section_obj)
    for task in tasks:
        task_id = task['id']
        complete_or_incomplete = "complete" if completed else "incomplete"
        print(f"marking {task_id} as {complete_or_incomplete}", end="...")
        response = s.put(f"https://app.asana.com/api/1.0/tasks/{task_id}", data={"completed": completed})
        if response.status_code != 200:
            print(f"failed")
            error = parse_asana_error_response(response)
            print(error, file=sys.stderr)
            sys.exit(1)
        else:
            print(f"success")

if __name__ == "__main__":
    main()
