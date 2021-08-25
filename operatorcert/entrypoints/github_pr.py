"""
Script for opening GitHub pull request
"""
import argparse
import logging
import os
from typing import Any, Dict

import giturlparse
import requests

LOGGER = logging.getLogger("operator-cert")


def setup_argparser() -> Any:
    """
    Setup argument parser

    Returns:
        Any: Initialized argument parser
    """
    parser = argparse.ArgumentParser(description="Github PR cli tool.")

    parser.add_argument(
        "--repository-url",
        required=True,
        help="Current/forked repository name",
    )

    parser.add_argument(
        "--repository-name",
        required=True,
        help="Upstream repository name",
    )
    parser.add_argument(
        "--target-branch",
        required=True,
        help="A targer branch for a PR",
    )
    parser.add_argument(
        "--source-branch",
        required=True,
        help="A source branch for a PR",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="A pull request title",
    )
    parser.add_argument(
        "--test-result-url",
        help="Preflight test result URL",
    )
    parser.add_argument(
        "--test-logs-url",
        help="Preflight test logs URL",
    )

    parser.add_argument(
        "--cert-project-id", help="Certification project ID", required=True
    )

    parser.add_argument(
        "--github-api-url", help="Github API URL", default="https://api.github.com"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser


def open_pr(
    github_api_url: str,
    repo_name: str,
    head: str,
    base: str,
    title: str,
    body: str,
) -> Dict[str, Any]:
    """
    Open new Github pull request

    Args:
        github_api_url (str): Github API URL
        repo_name (str): Repository name where the PR will be open
        head (str): Current git head that's used as a source for the PR
        base (str): A targer branch
        title (str): Pull request title
        body (str): Pull request body

    Raises:
        Exception: Raises exception when request fails

    Returns:
        Dict[str, Any]: Github API json response
    """

    pr_url = f"{github_api_url}/repos/{repo_name}/pulls"
    data = {"head": head, "base": base, "title": title, "body": body}

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise Exception("Github API token is missing. Set GITHUB_TOKEN env variable.")

    resp = requests.post(
        pr_url,
        json=data,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        LOGGER.error(f"Got error code from Github API {resp.status_code}")
        try:
            resp_msg = resp.json().get("message")
            LOGGER.error(f"{resp_msg}")
            LOGGER.debug(resp.json())
        except Exception:
            pass
        raise
    return resp.json()


def get_head(repository_url: str, branch: str) -> str:
    """
    Get source git head based on repo url and current branch

    Args:
        repository_url (str): Git repository URL
        branch (str): Git branch

    Returns:
        str: Git head for PR that serves as a source
    """
    parsed_url = giturlparse.parse(repository_url)
    path = parsed_url.owner

    namespace = path.split("/")[0]
    return f"{namespace}:{branch}"


def get_pr_body(args: Any) -> str:
    """
    Create a pull request body

    Args:
        args (Any): CLI arguments

    Returns:
        str: Pull request text body
    """
    title_parts = args.title.split()
    body = "**New operator bundle**\n\n"

    body += f"Name: **{title_parts[1]}**\n"
    body += f"Version: **{title_parts[2][1:-1]}**\n\n"
    body += f"Certification project: {args.cert_project_id}\n\n"

    if args.test_result_url:
        body += f"Test result URL: {args.test_result_url}\n"
    if args.test_logs_url:
        body += f"Test logs URL: {args.test_logs_url}\n"
    return body


def main() -> None:
    """
    Main function
    """
    parser = setup_argparser()
    args = parser.parse_args()

    log_level = "INFO"
    if args.verbose:
        log_level = "DEBUG"
    logging.basicConfig(level=log_level)

    pr_body = get_pr_body(args)
    head = get_head(args.repository_url, args.source_branch)
    response = open_pr(
        args.github_api_url,
        args.repository_name,
        head,
        args.target_branch,
        args.title,
        pr_body,
    )
    url = response.get("url")
    LOGGER.info(f"Pull request URL: {url}")


if __name__ == "__main__":
    main()
