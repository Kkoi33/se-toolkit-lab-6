# Lab setup

- [1. Required steps](#1-required-steps)
  - [1.1. Find a partner](#11-find-a-partner)
  - [1.2. Start creating a VM](#12-start-creating-a-vm)
  - [1.3. Set up your fork](#13-set-up-your-fork)
    - [1.3.1. Sign in on `GitHub`](#131-sign-in-on-github)
    - [1.3.2. Fork the course instructors' repo](#132-fork-the-course-instructors-repo)
    - [1.3.3. Go to your fork](#133-go-to-your-fork)
    - [1.3.4. Enable issues](#134-enable-issues)
    - [1.3.5. Add a classmate as a collaborator](#135-add-a-classmate-as-a-collaborator)
    - [1.3.6. Protect your `main` branch](#136-protect-your-main-branch)
  - [1.4. Set up programs](#14-set-up-programs)
    - [1.4.1. Set up `VS Code`](#141-set-up-vs-code)
    - [1.4.2. Set up `Docker`](#142-set-up-docker)
    - [1.4.3. (`Windows` only) Switch to the `Linux` shell for the `VS Code Terminal`](#143-windows-only-switch-to-the-linux-shell-for-the-vs-code-terminal)
    - [1.4.4. Clean up `Docker`](#144-clean-up-docker)
    - [1.4.5. Set up `Git`](#145-set-up-git)
  - [1.5. Open in `VS Code` the `software-engineering-toolkit` directory](#15-open-in-vs-code-the-software-engineering-toolkit-directory)
  - [1.6. Clone your fork](#16-clone-your-fork)
    - [1.6.1. Copy your fork URL](#161-copy-your-fork-url)
    - [1.6.2. Clone your fork](#162-clone-your-fork)
  - [1.7. Open the cloned repo and set up `VS Code`](#17-open-the-cloned-repo-and-set-up-vs-code)
  - [1.8. Continue creating a VM](#18-continue-creating-a-vm)
  - [1.9. Set up `Python`](#19-set-up-python)
    - [1.9.1. Install `uv`](#191-install-uv)
    - [1.9.2. Set up `Python` in `VS Code`](#192-set-up-python-in-vs-code)
  - [1.10. Set up the environment (on your laptop)](#110-set-up-the-environment-on-your-laptop)
  - [1.11. Clean up the previous lab (on your VM)](#111-clean-up-the-previous-lab-on-your-vm)
  - [1.12. Deploy to your VM](#112-deploy-to-your-vm)
    - [1.12.1. Connect to your VM and clone the repo](#1121-connect-to-your-vm-and-clone-the-repo)
    - [1.12.2. Prepare the environment (on the VM)](#1122-prepare-the-environment-on-the-vm)
    - [1.12.3. Start the services (on the VM)](#1123-start-the-services-on-the-vm)
  - [1.13. Populate the database](#113-populate-the-database)
  - [1.14. Verify the deployment](#114-verify-the-deployment)
  - [1.15. Set up a coding agent](#115-set-up-a-coding-agent)
- [2. Optional steps](#2-optional-steps)
  - [2.1. Set up `Nix`](#21-set-up-nix)
  - [2.2. Set up `direnv`](#22-set-up-direnv)
  - [2.3. Learn to go back after clicking a link](#23-learn-to-go-back-after-clicking-a-link)
  - [2.4. Set up the shell prompt](#24-set-up-the-shell-prompt)
  - [2.5. Customize the `Source Control`](#25-customize-the-source-control)
  - [2.6. Get familiar with `GitLens`](#26-get-familiar-with-gitlens)
  - [2.7. Create a label for tasks](#27-create-a-label-for-tasks)
  - [2.8. View `Markdown` files in `VS Code`](#28-view-markdown-files-in-vs-code)

## 1. Required steps

> [!IMPORTANT]
> This is the full setup guide. If you completed Labs 4–5 and already have
> all tools installed, use [setup-simple.md](setup-simple.md) instead.

> [!NOTE]
> We provide all of the hardest steps in the lab setup
> so that TAs can help you get the right setup during the lab.
>
> Tasks are more or less easy when you have the right setup.

> [!NOTE]
> This lab needs your university email, GitHub alias, and VM IP in the Autochecker bot <https://t.me/auchebot>. If you haven't registered, do so now. If you want to change something, contact your TA.

### 1.1. Find a partner

1. Find a partner for this lab.
2. Sit next to them.

> [!IMPORTANT]
> You work on tasks independently from your partner.
>
> You and your partner work together when reviewing each other's work.

### 1.2. Start creating a VM

> [!NOTE]
> Skip this step if you can [connect to your VM](../../wiki/vm.md#connect-to-the-vm).

[Create a subscription](../../wiki/vm.md#create-a-subscription) to be able to create a VM.

> [!TIP]
> Subscription approval may take time.
> Continue with the next steps while you wait — you will
> [finish creating the VM](#18-continue-creating-a-vm) later.

### 1.3. Set up your fork

#### 1.3.1. Sign in on `GitHub`

1. Sign in on [`GitHub`](https://github.com/).
2. [Find `<your-github-username>`](../../wiki/github.md#find-your-github-username).

#### 1.3.2. Fork the course instructors' repo

1. [Fork the course instructors' repo](../../wiki/github.md#fork-a-repo).

   The course instructors' repo [URL](../../wiki/computer-networks.md#url) is <https://github.com/inno-se-toolkit/se-toolkit-lab-6>.

#### 1.3.3. Go to your fork

1. [Go to your fork](../../wiki/github.md#go-to-your-fork).

   The [URL](../../wiki/computer-networks.md#url) of your fork should look like `https://github.com/<your-github-username>/se-toolkit-lab-6`.

#### 1.3.4. Enable issues

1. [Enable issues](../../wiki/github.md#enable-issues).

#### 1.3.5. Add a classmate as a collaborator

1. [Add a collaborator](../../wiki/github.md#add-a-collaborator) — your partner.
2. Your partner should add you as a collaborator in their repo.

> [!NOTE]
> It's OK if your collaborator can't change `Settings` in your repo.

#### 1.3.6. Protect your `main` branch

> [!NOTE]
> Branch protection prevents accidental pushes directly to `main`.
> This enforces the PR workflow and ensures all changes are reviewed.

1. [Protect the `main` branch](../../wiki/github.md#protect-a-branch).

### 1.4. Set up programs

#### 1.4.1. Set up `VS Code`

1. (Optional) [Read about `VS Code`](../../wiki/vs-code.md#what-is-vs-code).
2. [Set up `VS Code`](../../wiki/vs-code.md#set-up-vs-code).

#### 1.4.2. Set up `Docker`

1. (Optional) [Read about `Docker`](../../wiki/docker.md#what-is-docker).
2. [Install `Docker`](../../wiki/docker.md#install-docker) if it's not installed.
3. [Start `Docker`](../../wiki/docker.md#start-docker).

#### 1.4.3. (`Windows` only) Switch to the `Linux` shell for the `VS Code Terminal`

1. [Check the current shell in the `VS Code Terminal`](../../wiki/vs-code.md#check-the-current-shell-in-the-vs-code-terminal).
2. If it's not `bash` or `zsh`, [switch to the `Linux` shell for the `VS Code Terminal`](../../wiki/vs-code.md#windows-only-switch-to-the-linux-shell-for-the-vs-code-terminal).
3. [Check the current shell](../../wiki/vs-code.md#check-the-current-shell-in-the-vs-code-terminal) again.

#### 1.4.4. Clean up `Docker`

1. [Clean up `Docker`](../../wiki/docker.md#clean-up-docker).

   **Note:** Old containers and volumes from a previous lab version may conflict with the updated services.
   Stop running containers, remove stopped containers, and delete unused volumes so you start with a clean state.

#### 1.4.5. Set up `Git`

1. (Optional) [Read about `Git`](../../wiki/git.md#what-is-git).
2. [Install `Git`](https://git-scm.com/install/) if it's not installed.
3. (Optional) [Configure `Git`](../../wiki/git.md#configure-git).

### 1.5. Open in `VS Code` the `software-engineering-toolkit` directory

1. Inside the [`Desktop` directory](../../wiki/file-system.md#desktop-directory),
   create the directory `software-engineering-toolkit`.

   Skip this step if this directory exists.

2. [Open in `VS Code` the directory](../../wiki/vs-code.md#open-the-directory):
   `software-engineering-toolkit`.
3. (`Windows` only) [Reopen the directory in `WSL`](../../wiki/vs-code.md#windows-only-reopen-the-directory-in-wsl) if you didn't do that before.

### 1.6. Clone your fork

#### 1.6.1. Copy your fork URL

1. [Go to your fork](#133-go-to-your-fork).
2. Copy [`<your-fork-url>`](../../wiki/github.md#your-fork-url).

   It should look like `https://github.com/<your-github-username>/se-toolkit-lab-6`.

   See [`<your-github-username>`](../../wiki/github.md#your-github-username).

#### 1.6.2. Clone your fork

1. [Clone your fork](../../wiki/git-vscode.md#clone-the-repository):

   - Replace `<repo-url>` with [`<your-fork-url>`](../../wiki/github.md#your-fork-url).
   - Replace `<repo-name>` with `se-toolkit-lab-6`.

### 1.7. Open the cloned repo and set up `VS Code`

> [!IMPORTANT]
> Go by the links in the steps below and complete the checks ("You should see ...").
> Otherwise, your setup will be broken.

1. [Open in `VS Code` the directory](../../wiki/vs-code.md#open-the-directory):
   `se-toolkit-lab-6`.
2. [Check the current shell in the `VS Code Terminal`](../../wiki/vs-code.md#check-the-current-shell-in-the-vs-code-terminal).
3. [Install the recommended `VS Code` extensions](../../wiki/vs-code.md#install-the-recommended-vs-code-extensions).

<details><summary><b>Troubleshooting (click to open)</b></summary>

<h4>The terminal shell is not <code>bash</code> or <code>zsh</code></h4>

Go back to [step 1.4.3](#143-windows-only-switch-to-the-linux-shell-for-the-vs-code-terminal) and set the default shell.

<h4>Recommended extensions did not install</h4>

Reload the `VS Code` window: press `Ctrl+Shift+P`, type `Reload Window`, and press `Enter`.

</details>

### 1.8. Continue creating a VM

> [!NOTE]
> Don't overwrite the key if it already exists.
> You can use the key that you created before for the new VM.

If you can't [connect to your VM](../../wiki/vm.md#connect-to-the-vm), complete these steps:

1. [Set up `SSH`](../../wiki/ssh.md#set-up-ssh).
2. [Create a VM using the subscription](../../wiki/vm.md#create-a-vm-using-the-subscription).

### 1.9. Set up `Python`

> [!NOTE]
> See [What is `Python`](../../wiki/python.md#what-is-python).

#### 1.9.1. Install `uv`

> [!NOTE]
> See [`uv`](../../wiki/python.md#uv).

1. [Install `uv`](../../wiki/python.md#install-uv).

#### 1.9.2. Set up `Python` in `VS Code`

1. [Set up `Python` in `VS Code`](../../wiki/python.md#set-up-python-in-vs-code).

### 1.10. Set up the environment (on your laptop)

1. Go to `VS Code Terminal`, [check that the current directory is `se-toolkit-lab-6`](../../wiki/shell.md#check-the-current-directory-is-directory-name), and install `Python` dependencies:

   ```terminal
   uv sync --dev
   ```

2. Create the environment file:

   ```terminal
   cp .env.docker.example .env.docker.secret
   ```

3. Configure the autochecker API credentials.

   The ETL pipeline fetches data from the autochecker dashboard API.
   Open `.env.docker.secret` and set:

   ```text
   AUTOCHECKER_EMAIL=<your-email>@innopolis.university
   AUTOCHECKER_PASSWORD=<your-github-username><your-telegram-alias>
   ```

   Example: if your GitHub username is `johndoe` and your Telegram alias is `jdoe`, the password is `johndoejdoe`.

   > [!IMPORTANT]
   > The credentials must match your autochecker bot registration.

### 1.11. Clean up the previous lab (on your VM)

> [!IMPORTANT]
> Remove previous lab containers and volumes to free up ports and disk space on your VM.

1. [Connect to your VM](../../wiki/vm.md#connect-to-the-vm).
2. Navigate to the previous lab's project directory:

   ```terminal
   cd ~/se-toolkit-lab-5
   ```

3. Stop and remove all containers and volumes:

   ```terminal
   docker compose --env-file .env.docker.secret down -v
   ```

4. Go back to the home directory:

   ```terminal
   cd ~
   ```

> [!NOTE]
> If you didn't do Lab 5, try `cd ~/se-toolkit-lab-4` instead.
> If neither directory exists, skip this step.

### 1.12. Deploy to your VM

#### 1.12.1. Connect to your VM and clone the repo

1. Connect to your VM:

   ```terminal
   ssh <vm-user>@<vm-ip>
   ```

   If unable, see [how to connect to your VM](../../wiki/vm.md#connect-to-the-vm).

2. Clone your fork on the VM:

   ```terminal
   cd ~
   git clone https://github.com/<your-github-username>/se-toolkit-lab-6.git
   cd se-toolkit-lab-6
   ```

#### 1.12.2. Prepare the environment (on the VM)

1. Create the `Docker` environment file:

   ```terminal
   cp .env.docker.example .env.docker.secret
   ```

2. Edit `.env.docker.secret`:

   ```terminal
   nano .env.docker.secret
   ```

   Set your autochecker API credentials:

   ```text
   AUTOCHECKER_EMAIL=<your-email>@innopolis.university
   AUTOCHECKER_PASSWORD=<your-github-username><your-telegram-alias>
   ```

   Set `LMS_API_KEY` — this is the **backend API key** that protects your LMS endpoints (used for `Authorization: Bearer` in Swagger and the frontend). It is **not** the LLM key — that comes later in Task 1.

   ```text
   LMS_API_KEY=set-it-to-something-and-remember-it
   ```

   Save and exit: `Ctrl+X`, then `y`, then `Enter`.

#### 1.12.3. Start the services (on the VM)

1. Start the services in the background:

   ```terminal
   docker compose --env-file .env.docker.secret up --build -d
   ```

2. Check that the containers are running:

   ```terminal
   docker compose --env-file .env.docker.secret ps --format "table {{.Service}}\t{{.Status}}"
   ```

   You should see all four services running:

   ```terminal
   SERVICE    STATUS
   app        Up 50 seconds
   caddy      Up 49 seconds
   pgadmin    Up 50 seconds
   postgres   Up 55 seconds (healthy)
   ```

   <details><summary><b>Troubleshooting (click to open)</b></summary>

   <h4>Port conflict (<code>port is already allocated</code>)</h4>

   [Clean up `Docker`](../../wiki/docker.md#clean-up-docker), then run the `docker compose up` command again.

   <h4>Containers exit immediately</h4>

   Rebuild all containers from scratch:

   ```terminal
   docker compose --env-file .env.docker.secret down -v
   docker compose --env-file .env.docker.secret up --build -d
   ```

   <h4>Image pull fails</h4>

   Check your internet connection. If you are behind a proxy, configure `Docker` to use it.

   </details>

### 1.13. Populate the database

The database starts empty. You need to run the ETL pipeline to populate it with data from the autochecker API.

1. Open in a browser: `http://<your-vm-ip>:42002/docs`

   You should see the Swagger UI page.

2. [Authorize in Swagger](../../wiki/swagger.md#authorize-in-swagger-ui) with the `LMS_API_KEY` you set in `.env.docker.secret`.

3. Run the ETL sync by calling `POST /pipeline/sync` in Swagger UI.

   You should get a response showing the number of items and logs loaded:

   ```json
   {
     "items_loaded": 120,
     "logs_loaded": 5000
   }
   ```

   > [!NOTE]
   > The exact numbers depend on how much data the autochecker API has.
   > As long as both numbers are greater than 0, the sync worked.

4. Verify data by calling `GET /items/`.

   You should get a non-empty array of items.

### 1.14. Verify the deployment

1. Open `http://<your-vm-ip>:42002/docs` in a browser.

   You should see the Swagger UI with all endpoints.

2. Open `http://<your-vm-ip>:42002/` in a browser.

   You should see the frontend. Enter your API key to connect.

3. Switch to the **Dashboard** tab.

   You should see charts with analytics data (score distribution, submissions timeline, group performance, task pass rates).

> [!IMPORTANT]
> If the dashboard shows no data or errors, make sure:
> - The ETL sync completed successfully (step 1.13)
> - You entered the correct API key in the frontend
> - Try selecting a different lab in the dropdown (e.g., `lab-04`)

### 1.15. Set up a coding agent

A coding agent can help you write code, explain concepts, and debug issues.

- Method 1: [Set up a `Qwen Code`-based agent](../../wiki/qwen.md#set-up-qwen-code).
- Method 2: [Choose another coding agent](../../wiki/coding-agents.md#choose-and-use-a-coding-agent).

---

## 2. Optional steps

These enhancements can make your life easier:

<!-- no toc -->
- [Set up `Nix`](#21-set-up-nix)
- [Set up `direnv`](#22-set-up-direnv)
- [Learn to go back after clicking a link](#23-learn-to-go-back-after-clicking-a-link)
- [Set up the shell prompt](#24-set-up-the-shell-prompt)
- [Customize the `Source Control`](#25-customize-the-source-control)
- [Get familiar with `GitLens`](#26-get-familiar-with-gitlens)
- [Create a label for tasks](#27-create-a-label-for-tasks)
- [View `Markdown` files in `VS Code`](#28-view-markdown-files-in-vs-code)

### 2.1. Set up `Nix`

1. (Optional) [Read about `Nix`](../../wiki/nix.md#what-is-nix).
2. [Set up `Nix`](../../wiki/nix.md#set-up-nix).

### 2.2. Set up `direnv`

1. (Optional) [Read about `direnv`](../../wiki/direnv.md#what-is-direnv).
2. [Set up `Nix`](#21-set-up-nix).
3. [Set up `direnv`](../../wiki/direnv.md#set-up-direnv).

### 2.3. Learn to go back after clicking a link

> [!NOTE]
> Shortcuts for going back after clicking a link:
>
> - `VS Code` — see the [shortcut](../../wiki/vs-code.md#shortcut-go-back).
> - `Firefox` — `Alt+ArrowLeft`.
> - Other browsers — google.

### 2.4. Set up the shell prompt

`Starship` shows your current `Git` branch, status, and other useful info directly in your [shell prompt](../../wiki/shell.md#shell-prompt) in almost any terminal, including the [`VS Code Terminal`](../../wiki/vs-code.md#vs-code-terminal).

Complete these steps:

1. [Install `Starship`](https://github.com/starship/starship#-installation).
2. [Open the `VS Code Terminal`](../../wiki/vs-code.md#open-the-vs-code-terminal).

   You should see something similar to this:

   <img alt="Starship in the VS Code Terminal" src="../../wiki/images/starship/terminal-prompt.png" style="width:400px"></img>

### 2.5. Customize the `Source Control`

1. [Open the `Source Control`](../../wiki/vs-code.md#open-the-source-control).
2. Click three dots to the right of `SOURCE CONTROL`.
3. Put checkmarks only near `Changes` and `GitLens` to see only these views.

   <img alt="Changes and GitLens" src="../../wiki/images/vs-code/source-control-allowed-views.png" style="width:400px"></img>

### 2.6. Get familiar with `GitLens`

[`GitLens`](../../wiki/gitlens.md#what-is-gitlens) helps you work with `Git` in `VS Code`.

Complete these steps:

1. [See all branches](../../wiki/gitlens.md#see-all-branches).
2. [Look at the commit graph](../../wiki/gitlens.md#look-at-the-commit-graph).
3. [Inspect the current branch](../../wiki/gitlens.md#inspect-the-current-branch).
4. [Inspect the remotes](../../wiki/gitlens.md#inspect-the-remotes).

### 2.7. Create a label for tasks

[Labels](../../wiki/github.md#label) help you filter and organize issues.

With a `task` label, you can see in one view all issues created for lab tasks.

> [!TIP]
> If you create the `task` label before creating issues, your issues will have this label automatically as configured in the [issue form](../../.github/ISSUE_TEMPLATE/01-task.yml).

Complete these steps:

1. [Create](../../wiki/github.md#create-a-label) the `task` label.
2. [Add the label to issues](../../wiki/github.md#add-a-label-to-issues).
3. [See all issues with the label](../../wiki/github.md#see-all-issues-with-a-label).

### 2.8. View `Markdown` files in `VS Code`

If you want to view [`README.md`](../../README.md) and other `Markdown` files in `VS Code` instead of on `GitHub`:

1. [Install the recommended `VS Code` extensions](../../wiki/vs-code.md#install-the-recommended-vs-code-extensions).
2. [Open the file](../../wiki/vs-code.md#open-the-file):
   [`README.md`](../../README.md).
3. [Open the `Markdown` preview](../../wiki/vs-code.md#open-the-markdown-preview).
