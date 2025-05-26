import argparse
import os
import subprocess
import sys

def run_script(command, capture_output=False, text=True, check=True, env=None):
    """Helper function to run a script using subprocess."""
    if env is None:
        env = os.environ.copy()
    
    # Ensure the command uses sys.executable for portability
    if not command[0].endswith(".py"):
         # Assume it's a script in the current dir, make it explicit with python interpreter
        command = [sys.executable] + command
    elif not command[0].startswith(sys.executable): # if it's a .py but not called with python
        command = [sys.executable] + command


    print(f"Running command: {' '.join(command)}")
    try:
        process = subprocess.run(
            command,
            capture_output=capture_output,
            text=text,
            check=check, # Will raise CalledProcessError for non-zero exit codes
            env=env
        )
        return process
    except FileNotFoundError as fnf_error:
        print(f"Error: Script not found - {fnf_error.filename}. Make sure it's in the correct path and executable.")
        return None
    except subprocess.CalledProcessError as cpe:
        print(f"Error running script: {' '.join(command)}")
        print(f"Return code: {cpe.returncode}")
        if cpe.stdout:
            print(f"Stdout: {cpe.stdout.strip()}")
        if cpe.stderr:
            print(f"Stderr: {cpe.stderr.strip()}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while trying to run {' '.join(command)}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Main daily workflow to discover topics, generate, and publish blog posts.")
    parser.add_argument(
        "--num_posts",
        type=int,
        default=2,
        help="Number of blog posts to generate and publish (default: 2)."
    )
    parser.add_argument(
        "--country",
        type=str,
        default='us',
        help="Country code for topic discovery (e.g., 'us', 'gb', default: 'us')."
    )
    args = parser.parse_args()

    if args.num_posts <= 0:
        print("Error: --num_posts must be a positive integer.")
        sys.exit(1)

    print("Starting daily workflow...")
    print(f"Goal: Generate and publish {args.num_posts} post(s) for country '{args.country}'.")

    # 1. Call discover_topics.py
    print("\nStep 1: Discovering topics...")
    discover_command = [
        'discover_topics.py',
        '--num_topics', str(args.num_posts),
        '--country', args.country
    ]
    discover_process = run_script(discover_command, capture_output=True)

    if not discover_process or discover_process.returncode != 0:
        print("Failed to discover topics. Exiting workflow.")
        sys.exit(1)

    # Parse topics from stdout
    # Expected output: "Top Topics from NewsAPI:" followed by lines like "1. Topic Title"
    # Or, if NEWSAPI_KEY is not set, it will print info messages then sample topics.
    
    raw_topics_output = discover_process.stdout.strip()
    print(f"Raw output from discover_topics.py:\n{raw_topics_output}")
    
    discovered_topics = []
    # A simple parsing logic: look for lines starting with a number and a dot.
    # This should be robust enough for sample and actual outputs.
    for line in raw_topics_output.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and (line[1] == '.' or line[2] == '.'): # "1. Topic" or "10. Topic"
            # Remove the leading number and dot (e.g., "1. ")
            topic_title = line.split('.', 1)[-1].strip()
            if topic_title:
                discovered_topics.append(topic_title)
    
    if not discovered_topics:
        print("No topics were successfully parsed from discover_topics.py output. Exiting workflow.")
        sys.exit(1)
        
    print(f"Successfully discovered {len(discovered_topics)} topics.")

    generated_posts_count = 0
    for i, topic in enumerate(discovered_topics):
        if i >= args.num_posts: # Ensure we don't generate more than requested if discover_topics returned more
            break
        
        print(f"\nProcessing topic {i+1}/{len(discovered_topics)}: \"{topic}\"")

        # 2. Call generate_post.py for each topic
        print(f"Step 2: Generating post for topic: \"{topic}\"...")
        generate_command = ['generate_post.py', topic]
        # Pass current environment (includes OPENAI_API_KEY if set)
        generate_process = run_script(generate_command, capture_output=True, env=os.environ.copy())

        if not generate_process or generate_process.returncode != 0:
            print(f"Failed to generate post for topic: \"{topic}\". Skipping this topic.")
            continue

        # Extract the generated Markdown filename from stdout
        # generate_post.py should print "Generated filename: <basename>"
        markdown_filename = None
        if generate_process and generate_process.stdout: # Check stdout exists before processing
            for line in generate_process.stdout.strip().splitlines():
                if line.startswith("Generated filename:"):
                    markdown_filename = line.split(":", 1)[-1].strip()
                    break
        
        if not markdown_filename:
            print(f"Could not determine Markdown filename for topic: \"{topic}\". Skipping publishing for this topic.")
            continue
        
        print(f"Markdown file '{markdown_filename}' generated successfully for topic \"{topic}\".")

        # 3. Call publish_post.py
        print(f"Step 3: Publishing post '{markdown_filename}'...")
        publish_command = ['publish_post.py', markdown_filename]
        publish_process = run_script(publish_command) # No output capture needed unless debugging

        if not publish_process or publish_process.returncode != 0:
            print(f"Failed to publish post '{markdown_filename}'.")
            # Decide if this is critical enough to stop the whole workflow. For now, just log and continue.
        else:
            print(f"Post '{markdown_filename}' published successfully.")
            generated_posts_count += 1

    print(f"\nDaily workflow completed. Successfully generated and processed {generated_posts_count} post(s).")

if __name__ == "__main__":
    # Ensure scripts are executable (useful if not calling via python explicitly)
    # This can be done beforehand or checked here. For now, assume they are,
    # or that calling with sys.executable handles it.
    # Example: os.chmod('discover_topics.py', 0o755)
    
    # Note: API keys (OPENAI_API_KEY, NEWSAPI_KEY) should be set in the environment
    # where this main_daily_workflow.py script is run.
    # The scripts themselves have fallback mechanisms if keys are not found.
    if not os.getenv("OPENAI_API_KEY"):
        print("INFO: OPENAI_API_KEY is not set. `generate_post.py` will use placeholder content.")
    if not os.getenv("NEWSAPI_KEY"):
        print("INFO: NEWSAPI_KEY is not set. `discover_topics.py` will use sample topics.")
        
    main()
