# Tables in the database
## The config table
- **Model name:** Config
- **Table name:** config
- **Table logic:** Every property/channel-configuration has a name and value
- **Commands:** 
    - `Config.set_init(name, value)`
        * Sets the `name` to `value` if `name` doesn't exist in DB
    - `Config.set(name, value)`
        * Sets the `name` to `value` regardless
    - `Config.get_key(name)`
        * Gets the `name`, returns `None` if `name` doesn't exist in DB
    - `Config.get(name)`
        * Gets the value of `name`, returns `None` if `name` doesn't exist in DB
    - `Config.channels()`
        * Returns all configs ending with `-channel` suffix

- __Warning__: Use `set_init` in main.py to keep a track of what configs we utilize. 
Do not use `set` directly without first declaring the config with `set_init`.

## The users table
- **Model name:** User
- **Table name:** users
- **Table logic:** A user can have multiple GitHub usernames for different teams but the same GitHub username for each
team. The unique key isn't a certain property of a Discord user, but rather a generated `unique_id`. Each user row has 
one team in [the teams table](#the-teams-table)
- **Properties:**
    - `User.user_id`
        - The id of the specified user
    - `User.user_team`
        - The team in which the specified user is enrolled (multiple User rows of the same user can exist for different
        teams)
    - `User.user_github`
        - The GitHub username of the specified user in the specified team (use the github id in the code)
    - `User.user_github_id`
        - The GitHub id of the specified user in the specified team
    - `User.team`
        - A relationship that references the Team model and back populates the users property in the teams table
- **Commands:**
    - `User.get(name, team_name)`
        - Gets the `User` with the specified `name` and `team_name`
    - `User.set(user_id, user_team, user_github)`
        - Sets a row for the user with the specified `user_id`, `user_team` and `user_github`
    - `User.get_teams()`
        - Gets all the teams in the database
    - `User.get_team(team_name)`
        - Gets the User objects which have the `User.user_team` as `team_name`
    - `User.delete_team(team_name)`
        - Deletes all the User objects which have the `User.user_team` as `team_name`
    - `User.delete(user_id, team_name)`
        - Deletes a certain User row which has `User.user_id` as `user_id` and `User.user_team` as `team_name`
        
## The warnings table
- **Model name:** Warn
- **Table name:** warns
- **Table logic:** Each user has a certain number of warns
- **Properties:**
    - `Warn.user_id`
        - The user id of the user that has more than 0 warns
    - `Warn.warns`
        - The number of warnings for the user
- **Commands:**
    - `Warn.get(user_id)`
        - Gets the Warn object of a user with a certain id or `None` if it doesn't exist.
    - `Warn.warn(user_id)`
        - Increases the `Warn.warns` of the user by 1 if the `Warn` object of `user_id` is found; otherwise, it would
        create a new `Warn` object of `Warn.warns` = 1 and `Warn.user_id` = `User_id`
    - `Warn.unwarn(user_id)`
        - Decreases the `Warn.warns` of the user by 1 and deletes him from the table if the `Warn.warns` becomes `0`
    - `Warn.warnings(user_id)`
        - Gets the number of warnings for the user and if the `Warn` object of `user_id` is not found, it returns `0`
    - `Warn.delete(user_id)`
        - Removes the `Warn` row of `user_id` from the table

## The teams table
- **Model name:** Team
- **Table name:** teams
- **Table logic:** A team has many users in the users table
- **Properties:**
    - `Team.team_name` (primary key)
        - The name of the team
    - `Team.role_id`
        - The id of the discord role of the team members
    - `Team.leader_role_id`
        - The id of the discord role of the team leader
    - `Team.category_id`
        - The id of the discord category of the team
    - `Team.general_id`
        - The id of the discord general text channel of the team
    - `Team.voting_id`
        - The id of the discord leader-voting text channel of the team
    - `Team.github_id`
        - The Github id of the team
    - `Team.repo_id`
        - The Github id of the repository on which the team works
    - `Team.users`
        - A relationship that references the User model and back populates the team property in the users table
- **Commands:**
    - `Team.get(team_name: str = None, github_id: int = None, category_id: int = None)`
        - Gets the team object by either the name, the github_id or the category_id or gets all of the teams if no arguments
        are provided
    - `Team.get_all()`
        - Gets a list of all the team objects
    - `Team.set(team_name, role_id, leader_role_id, category_id, general_id, github_id, repo_id)`
        - Sets a new team row in the database with the provided data, the voting_id defaults to -1 which means there is 
        no leader voting channel
    - `Team.set_voting_channel(team_name, voting_id)`
        - Sets the leader-voting channel of a certain team
    - `Team.delete_voting_channel(team_name)`
        - Deletes the leader-voting channel of a certain team
    - `Team.delete_team(team_name)`
        - Deletes the team from the database and all the related users from the users table