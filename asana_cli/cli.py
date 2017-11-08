import os
import json
import click
import requests
from functools import lru_cache

ASANA_TOKEN = os.environ['ASANA_TOKEN']

s = requests.Session()
s.headers = {"Authorization": f"Bearer {ASANA_TOKEN}"}

def get_item(item_type, items, name):
    try:
        return [x for x in items if x['name'] == name][0]
    except IndexError:
        raise Exception(f"unable to find {item_type} {name}")

def get_workspaces():
    response = s.get(f"https://app.asana.com/api/1.0/users/me")
    profile = response.json()['data']
    workspaces = profile['workspaces']
    return workspaces

def get_workspace(name):
    workspaces = get_workspaces()
    return get_item("workspace", workspaces, name)

def get_projects(workspace):
    workspace_id = workspace['id']
    response = s.get(f"https://app.asana.com/api/1.0/workspaces/{workspace_id}/projects")
    projects = response.json()['data']
    return projects

def get_project(name, workspace):
    projects = get_projects(workspace)
    return get_item("project", projects, name)

def get_sections(project):
    project_id = project['id']
    response = s.get(f"https://app.asana.com/api/1.0/projects/{project_id}/sections")
    sections = response.json()['data']
    return sections

def get_section(name, project):
    sections = get_sections(project)
    return get_item("section", sections, name)

def get_tasks(project, section=None):
    if section:
        section_id = section['id']
        response = s.get(f"https://app.asana.com/api/1.0/sections/{section_id}/tasks")
        tasks = response.json()['data']
    else:
        project_id = project['id']
        response = s.get(f"https://app.asana.com/api/1.0/projects/{project_id}/tasks")
        tasks = response.json()['data']
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

    response = s.get(f"https://app.asana.com/api/1.0/sections/{source_section_id}/tasks")
    response.raise_for_status()
    source_tasks = response.json()['data']

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
            error = response.json()
            raise Exception(str(error))
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
            error = response.json()
            raise Exception(str(error))
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
            error = response.json()
            raise Exception(str(error))
        else:
            print(f"success")

if __name__ == "__main__":
    main()