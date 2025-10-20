import os
import csv
import statistics
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats

def count_code_lines(directory_path, output_file_name):
    """
    Count lines of code in all files within each subdirectory of the given path.
    Writes results to CSV file one directory at a time for memory efficiency.
    
    Args:
        directory_path (str): Path to the directory to analyze
        
    Returns:
        str: Path to the generated CSV file
    """
    # Convert to Path object for easier handling
    root_path = Path(directory_path)
    
    if not root_path.exists():
        print("Available functions:")
        print("1. count_code_lines(directory_path) - Count lines of code in subdirectories")
        print("2. map_lines_to_project(projects_csv, codelines_csv) - Map code lines to projects")
        print("3. group_lines_by_categories(projects_with_codelines_csv) - Group code lines by region categories")
        print("4. draw_code_size_histograms(projects_with_codelines_csv) - Create histograms of code sizes")
        print("5. bugfix_recommendations_by_groups(projects_with_codelines_csv) - Group bugfix recommendations by categories")
        print("6. improving_code_recommendations_by_groups(projects_with_codelines_csv) - Group improving code recommendations by categories")
        print("7. draw_bugfix_boxplots(projects_with_codelines_csv) - Create boxplots of bugfix recommendations")
        print("8. stat_test(projects_with_codelines_csv) - Perform statistical tests on bugfix recommendations")
        raise ValueError(f"Directory {directory_path} does not exist")

    if not root_path.is_dir():
        raise ValueError(f"{directory_path} is not a directory")
    
    # # Common code file extensions
    # code_extensions = {
    #     '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', 
    #     '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
    #     '.html', '.css', '.scss', '.less', '.vue', '.jsx', '.tsx',
    #     '.sql', '.r', '.m', '.pl', '.sh', '.bash', '.zsh', '.ps1',
    #     '.xml', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'
    # }
    code_extensions = {'.java'}
    
    # Generate output CSV filename
    output_csv = root_path / output_file_name
    
    # Initialize CSV file with header
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['directory_name', 'code_lines']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    
    total_directories = 0
    total_lines_overall = 0
    
    # Get all subdirectories and sort them for consistent output
    subdirectories = [item for item in root_path.iterdir() if item.is_dir()]
    subdirectories.sort(key=lambda x: x.name)
    
    # Process each subdirectory one at a time (going 2 levels deep)
    for level1_dir in subdirectories:
        level1_name = level1_dir.name
        print(f"Processing level 1 directory: {level1_name}...")
        
        # Get subdirectories within the first level
        level2_subdirs = [item for item in level1_dir.iterdir() if item.is_dir()]
        level2_subdirs.sort(key=lambda x: x.name)
        
        for level2_dir in level2_subdirs:
            level2_name = level2_dir.name
            # Create combined directory name (e.g., "0xbb/otp-authenticator")
            combined_name = f"{level1_name}/{level2_name}"
            total_lines = 0
            
            print(f"  Processing project: {combined_name}...")
            
            # Recursively count lines in all code files in this project directory
            for file_path in level2_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in code_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = sum(1 for line in f if line.strip())  # Count non-empty lines
                        total_lines += lines
                    except (OSError, IOError, UnicodeDecodeError) as e:
                        # Skip files that can't be read
                        print(f"Warning: Could not read {file_path}: {e}")
                        continue
            
            # Write this project's result immediately to CSV
            with open(output_csv, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['directory_name', 'code_lines']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({
                    'directory_name': combined_name,  # Use the full path for matching (e.g., "0xbb/otp-authenticator")
                    'code_lines': total_lines
                })
            
            print(f"    {combined_name}: {total_lines} lines of code")
            total_directories += 1
            total_lines_overall += total_lines
    
    print(f"\nAnalysis complete! Results saved to: {output_csv}")
    print(f"Analyzed {total_directories} directories")
    print(f"Total lines across all directories: {total_lines_overall}")
    
    return str(output_csv)

def map_lines_to_project(projects_csv_path, codelines_csv_path, output_csv_path=None):
    """
    Map code lines data to projects by matching project names.
    
    Args:
        projects_csv_path (str): Path to the projects CSV file
        codelines_csv_path (str): Path to the code lines CSV file
        output_csv_path (str, optional): Path for output CSV. If None, creates 'projects_with_codelines.csv'
        
    Returns:
        str: Path to the generated CSV file
    """
    # Convert to Path objects
    projects_path = Path(projects_csv_path)
    codelines_path = Path(codelines_csv_path)
    
    # Validate input files
    if not projects_path.exists():
        raise ValueError(f"Projects CSV file {projects_csv_path} does not exist")
    
    if not codelines_path.exists():
        raise ValueError(f"Code lines CSV file {codelines_csv_path} does not exist")
    
    # Set output path if not provided
    if output_csv_path is None:
        output_csv_path = projects_path.parent / 'projects_with_codelines.csv'
    else:
        output_csv_path = Path(output_csv_path)
    
    # Read code lines data into a dictionary for fast lookup
    codelines_dict = {}
    try:
        with open(codelines_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Use directory_name as key, code_lines as value
                directory_name = row.get('directory_name', '').strip()
                code_lines = row.get('code_lines', '0').strip()
                if directory_name:
                    codelines_dict[directory_name] = code_lines
    except Exception as e:
        raise ValueError(f"Error reading code lines CSV: {e}") from e
    
    print(f"Loaded {len(codelines_dict)} code line entries")
    
    # Process projects CSV and add code_lines column
    matched_count = 0
    total_count = 0
    unmatched_projects = []  # Track unmatched projects
    
    try:
        with open(projects_path, 'r', encoding='utf-8') as input_file, \
             open(output_csv_path, 'w', newline='', encoding='utf-8') as output_file:
            
            reader = csv.DictReader(input_file)
            fieldnames = list(reader.fieldnames) + ['code_lines']
            
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                total_count += 1
                
                # Try to find a matching project name
                # Look for common project name fields
                project_name = None
                for field in ['name', 'project_name', 'directory_name', 'repo_name', 'project']:
                    if field in row and row[field]:
                        project_name = row[field].strip()
                        break
                
                # If no obvious field, try the first non-empty field
                if not project_name:
                    for field, value in row.items():
                        if value and value.strip():
                            project_name = value.strip()
                            break
                
                # Keep the full project path for matching (no splitting on '/')
                # This will match against entries like "0xbb/otp-authenticator"
                
                # Look up code lines
                code_lines = '0'  # Default value
                if project_name and project_name in codelines_dict:
                    code_lines = codelines_dict[project_name]
                    matched_count += 1
                    print(f"Matched: {project_name} -> {code_lines} lines")
                elif project_name:
                    unmatched_projects.append(project_name)
                    print(f"No match found for: {project_name}")
                
                # Add code_lines to the row
                row['code_lines'] = code_lines
                writer.writerow(row)
                
    except Exception as e:
        raise ValueError(f"Error processing CSV files: {e}") from e
    
    print("\nMapping complete!")
    print(f"Total projects processed: {total_count}")
    print(f"Successfully matched: {matched_count}")
    print(f"Unmatched projects: {total_count - matched_count}")
    print(f"Results saved to: {output_csv_path}")
    
    # Print all unmatched projects for debugging
    if unmatched_projects:
        print(f"\nList of {len(unmatched_projects)} unmatched projects:")
        for i, project in enumerate(unmatched_projects, 1):
            print(f"  {i}. {project}")
    else:
        print("\nAll projects were successfully matched!")
    
    return str(output_csv_path)

def group_lines_by_categories(projects_with_codelines_csv_path):
    """
    Group code lines by project categories based on stars_region, forks_region, and watchers_region.
    
    Args:
        projects_with_codelines_csv_path (str): Path to the projects_with_codelines.csv file
        
    Returns:
        dict: Dictionary containing 'lesser', 'medium', and 'high' lists of code line values
    """
    # Convert to Path object
    csv_path = Path(projects_with_codelines_csv_path)
    
    # Validate input file
    if not csv_path.exists():
        raise ValueError(f"CSV file {projects_with_codelines_csv_path} does not exist")
    
    # Initialize lists for each category
    lesser = []   # stars_region, forks_region, watchers_region all equal to 1
    medium = []   # stars_region, forks_region, watchers_region all equal to 2
    high = []     # stars_region, forks_region, watchers_region all equal to 3
    
    # Counters for statistics
    lesser_count = 0
    medium_count = 0
    high_count = 0
    other_count = 0
    total_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                total_count += 1
                
                # Get the region values
                stars_region = row.get('stars_region', '').strip()
                forks_region = row.get('forks_region', '').strip()
                watchers_region = row.get('watchers_region', '').strip()
                code_lines = row.get('code_lines', '0').strip()
                
                # Convert code_lines to integer, default to 0 if invalid
                try:
                    code_lines_int = int(code_lines)
                except (ValueError, TypeError):
                    code_lines_int = 0
                
                # Check if all three regions match the category criteria
                if stars_region == '1' and forks_region == '1' and watchers_region == '1':
                    lesser.append(code_lines_int)
                    lesser_count += 1
                elif stars_region == '2' and forks_region == '2' and watchers_region == '2':
                    medium.append(code_lines_int)
                    medium_count += 1
                elif stars_region == '3' and forks_region == '3' and watchers_region == '3':
                    high.append(code_lines_int)
                    high_count += 1
                else:
                    other_count += 1
                    
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}") from e
    
    # Print summary statistics
    print("Code lines grouped by categories:")
    print(f"  Lesser (1,1,1): {lesser_count} projects")
    print(f"  Medium (2,2,2): {medium_count} projects")
    print(f"  High (3,3,3): {high_count} projects")
    print(f"  Other combinations: {other_count} projects")
    print(f"  Total projects: {total_count}")
    
    # Print basic statistics for each category
    if lesser:
        print("\nLesser category statistics:")
        print(f"  Min: {min(lesser)}, Max: {max(lesser)}, Avg: {sum(lesser)/len(lesser):.2f}")
        print(f"  Standard Deviation: {statistics.stdev(lesser):.2f}")
    
    if medium:
        print("\nMedium category statistics:")
        print(f"  Min: {min(medium)}, Max: {max(medium)}, Avg: {sum(medium)/len(medium):.2f}")
        print(f"  Standard Deviation: {statistics.stdev(medium):.2f}")
    
    if high:
        print("\nHigh category statistics:")
        print(f"  Min: {min(high)}, Max: {max(high)}, Avg: {sum(high)/len(high):.2f}")
        print(f"  Standard Deviation: {statistics.stdev(high):.2f}")
    
    # Return the grouped data
    return {
        'lesser': lesser,
        'medium': medium,
        'high': high
    }

def draw_code_size_histograms(projects_with_codelines_csv_path, save_path=None):
    """
    Create separate histograms of code sizes for different project categories.
    
    Args:
        projects_with_codelines_csv_path (str): Path to the projects_with_codelines.csv file
        save_path (str, optional): Base path for saving figures. If None, uses default naming.
        
    Returns:
        dict: The grouped data used for plotting
    """
    # Get the grouped data
    data = group_lines_by_categories(projects_with_codelines_csv_path)
    
    # Define colors for each category
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']  # Red, Teal, Blue
    categories = ['lesser', 'medium', 'high']
    titles = ['Lesser-quality Projects', 'Medium-quality Projects', 'High-quality Projects']
    
    # Generate base filename if no save_path provided
    if save_path is None:
        # from datetime import datetime
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"code_size_histogram"
    else:
        # Remove .pdf extension if present and use as base
        base_filename = save_path.replace('.pdf', '')
    
    saved_files = []
    
    # Define consistent bin edges for all histograms
    import numpy as np
    bin_edges = np.linspace(0, 2.5e7, 21)  # 20 bins from 0 to 25 million
    
    # Create separate figure for each category
    for i, (category, title, color) in enumerate(zip(categories, titles, colors)):
        data_list = data[category]
        
        # Create new figure for this category
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        
        if data_list:  # Only plot if there's data
            ax.hist(data_list, bins=bin_edges, color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
            # ax.set_title(title, fontsize=20, fontweight='bold')
            ax.set_xlabel('Lines of Code (millions)', fontsize=20)
            ax.set_ylabel('Number of Projects', fontsize=20)
            ax.tick_params(axis='both', which='major', labelsize=14)  # Set tick label font size
            ax.set_xlim(0, 2.5 * 1e7)  # Set consistent x-axis scale to 1 million
            ax.set_yscale('log')  # Set y-axis to logarithmic scale
            ax.grid(True, alpha=0.3)
            
            # Add statistics text
            mean_val = sum(data_list) / len(data_list)
            std_val = statistics.stdev(data_list) if len(data_list) > 1 else 0
            stats_text = f'n={len(data_list)}\nMean: {mean_val:.0f}\nStd: {std_val:.0f}'
            ax.text(0.7, 0.95, stats_text, transform=ax.transAxes, fontsize=16,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        else:
            # If no data, show empty plot with message
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes,
                   horizontalalignment='center', verticalalignment='center',
                   fontsize=16, color='gray')
            ax.set_title(title, fontsize=16, fontweight='bold')
            ax.set_xlabel('Lines of Code', fontsize=16)
            ax.set_ylabel('Number of Projects', fontsize=16)
            ax.tick_params(axis='both', which='major', labelsize=14)  # Set tick label font size
            ax.set_xlim(0, 1e6)  # Set consistent x-axis scale to 1 million
        
        # Adjust layout
        plt.tight_layout()
        
        # Generate filename for this category
        filename = f"{base_filename}_{category}.pdf"
        
        # Save the figure
        plt.savefig(filename, dpi=300, bbox_inches='tight', format='pdf')
        saved_files.append(filename)
        print(f"Histogram for {title} saved to: {filename}")
        
        # Display the plot
        plt.show()
        
        # Close the figure to free memory
        plt.close(fig)
    
    # Print summary
    print(f"\nHistogram Summary:")
    for category, title in zip(categories, titles):
        count = len(data[category])
        print(f"  {title}: {count} projects")
    
    print(f"\nAll histograms saved:")
    for filename in saved_files:
        print(f"  {filename}")
    
    return data

def bugfix_recommendations_by_groups(projects_with_codelines_csv_path):
    """
    Group bugfix recommendations by project categories based on stars_region, forks_region, and watchers_region.
    
    Args:
        projects_with_codelines_csv_path (str): Path to the projects_with_codelines.csv file
        
    Returns:
        dict: Dictionary containing 'bugfixes_lesser', 'bugfixes_medium', and 'bugfixes_high' lists
    """
    # Convert to Path object
    csv_path = Path(projects_with_codelines_csv_path)
    
    # Validate input file
    if not csv_path.exists():
        raise ValueError(f"CSV file {projects_with_codelines_csv_path} does not exist")
    
    # Initialize lists for each category
    bugfixes_lesser = []   # stars_region, forks_region, watchers_region all equal to 1
    bugfixes_medium = []   # stars_region, forks_region, watchers_region all equal to 2
    bugfixes_high = []     # stars_region, forks_region, watchers_region all equal to 3
    
    # Counters for statistics
    lesser_count = 0
    medium_count = 0
    high_count = 0
    other_count = 0
    total_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                total_count += 1
                
                # Get the region values
                stars_region = row.get('stars_region', '').strip()
                forks_region = row.get('forks_region', '').strip()
                watchers_region = row.get('watchers_region', '').strip()
                bugfix = row.get('bugfix', '0').strip()
                
                # Convert bugfix to integer, default to 0 if invalid
                try:
                    bugfix_int = int(bugfix)
                except (ValueError, TypeError):
                    bugfix_int = 0
                
                # Check if all three regions match the category criteria
                if stars_region == '1' and forks_region == '1' and watchers_region == '1':
                    bugfixes_lesser.append(bugfix_int)
                    lesser_count += 1
                elif stars_region == '2' and forks_region == '2' and watchers_region == '2':
                    bugfixes_medium.append(bugfix_int)
                    medium_count += 1
                elif stars_region == '3' and forks_region == '3' and watchers_region == '3':
                    bugfixes_high.append(bugfix_int)
                    high_count += 1
                else:
                    other_count += 1
                    
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}") from e
    
    # Print summary statistics
    print("Bugfix recommendations grouped by categories:")
    print(f"  Lesser (1,1,1): {lesser_count} projects")
    print(f"  Medium (2,2,2): {medium_count} projects")
    print(f"  High (3,3,3): {high_count} projects")
    print(f"  Other combinations: {other_count} projects")
    print(f"  Total projects: {total_count}")
    
    # Print basic statistics for each category
    if bugfixes_lesser:
        print("\nLesser category bugfix statistics:")
        print(f"  Min: {min(bugfixes_lesser)}, Max: {max(bugfixes_lesser)}, Avg: {sum(bugfixes_lesser)/len(bugfixes_lesser):.4f}")
        print(f"  Standard Deviation: {statistics.stdev(bugfixes_lesser):.4f}")
    
    if bugfixes_medium:
        print("\nMedium category bugfix statistics:")
        print(f"  Min: {min(bugfixes_medium)}, Max: {max(bugfixes_medium)}, Avg: {sum(bugfixes_medium)/len(bugfixes_medium):.4f}")
        print(f"  Standard Deviation: {statistics.stdev(bugfixes_medium):.4f}")

    if bugfixes_high:
        print("\nHigh category bugfix statistics:")
        print(f"  Min: {min(bugfixes_high)}, Max: {max(bugfixes_high)}, Avg: {sum(bugfixes_high)/len(bugfixes_high):.4f}")
        print(f"  Standard Deviation: {statistics.stdev(bugfixes_high):.4f}")

    # Return the grouped data
    return {
        'bugfixes_lesser': bugfixes_lesser,
        'bugfixes_medium': bugfixes_medium,
        'bugfixes_high': bugfixes_high
    }

def improving_code_recommendations_by_groups(projects_with_codelines_csv_path):
    """
    Group improving code recommendations by project categories based on stars_region, forks_region, and watchers_region.
    
    Args:
        projects_with_codelines_csv_path (str): Path to the projects_with_codelines.csv file
        
    Returns:
        dict: Dictionary containing 'improvingcode_lesser', 'improvingcode_medium', and 'improvingcode_high' lists
    """
    # Convert to Path object
    csv_path = Path(projects_with_codelines_csv_path)
    
    # Validate input file
    if not csv_path.exists():
        raise ValueError(f"CSV file {projects_with_codelines_csv_path} does not exist")
    
    # Initialize lists for each category
    improvingcode_lesser = []   # stars_region, forks_region, watchers_region all equal to 1
    improvingcode_medium = []   # stars_region, forks_region, watchers_region all equal to 2
    improvingcode_high = []     # stars_region, forks_region, watchers_region all equal to 3
    
    # Counters for statistics
    lesser_count = 0
    medium_count = 0
    high_count = 0
    other_count = 0
    total_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                total_count += 1
                
                # Get the region values
                stars_region = row.get('stars_region', '').strip()
                forks_region = row.get('forks_region', '').strip()
                watchers_region = row.get('watchers_region', '').strip()
                improvingcode = row.get('improvingcode', '0').strip()
                
                # Convert improvingcode to integer, default to 0 if invalid
                try:
                    improvingcode_int = int(improvingcode)
                except (ValueError, TypeError):
                    improvingcode_int = 0
                
                # Check if all three regions match the category criteria
                if stars_region == '1' and forks_region == '1' and watchers_region == '1':
                    improvingcode_lesser.append(improvingcode_int)
                    lesser_count += 1
                elif stars_region == '2' and forks_region == '2' and watchers_region == '2':
                    improvingcode_medium.append(improvingcode_int)
                    medium_count += 1
                elif stars_region == '3' and forks_region == '3' and watchers_region == '3':
                    improvingcode_high.append(improvingcode_int)
                    high_count += 1
                else:
                    other_count += 1
                    
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}") from e
    
    # Print summary statistics
    print("Improving code recommendations grouped by categories:")
    print(f"  Lesser (1,1,1): {lesser_count} projects")
    print(f"  Medium (2,2,2): {medium_count} projects")
    print(f"  High (3,3,3): {high_count} projects")
    print(f"  Other combinations: {other_count} projects")
    print(f"  Total projects: {total_count}")
    
    # Print basic statistics for each category
    if improvingcode_lesser:
        print("\nLesser category improving code statistics:")
        print(f"  Min: {min(improvingcode_lesser)}, Max: {max(improvingcode_lesser)}, Avg: {sum(improvingcode_lesser)/len(improvingcode_lesser):.4f}")
        print(f"  Standard Deviation: {statistics.stdev(improvingcode_lesser):.4f}")
    
    if improvingcode_medium:
        print("\nMedium category improving code statistics:")
        print(f"  Min: {min(improvingcode_medium)}, Max: {max(improvingcode_medium)}, Avg: {sum(improvingcode_medium)/len(improvingcode_medium):.4f}")
        print(f"  Standard Deviation: {statistics.stdev(improvingcode_medium):.4f}")

    if improvingcode_high:
        print("\nHigh category improving code statistics:")
        print(f"  Min: {min(improvingcode_high)}, Max: {max(improvingcode_high)}, Avg: {sum(improvingcode_high)/len(improvingcode_high):.4f}")
        print(f"  Standard Deviation: {statistics.stdev(improvingcode_high):.4f}")

    # Return the grouped data
    return {
        'improvingcode_lesser': improvingcode_lesser,
        'improvingcode_medium': improvingcode_medium,
        'improvingcode_high': improvingcode_high
    }

def draw_bugfix_boxplots(projects_with_codelines_csv_path, save_path=None):
    """
    Create boxplots of bugfix recommendations for different project categories.
    
    Args:
        projects_with_codelines_csv_path (str): Path to the projects_with_codelines.csv file
        save_path (str, optional): Path to save the figure. If None, uses default naming.
        
    Returns:
        dict: The grouped bugfix data used for plotting
    """
    # Get the grouped bugfix data
    data = bugfix_recommendations_by_groups(projects_with_codelines_csv_path)
    
    # Prepare data for boxplot
    boxplot_data = []
    labels = []
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']  # Red, Teal, Blue
    
    # Add data for each category that has entries
    if data['bugfixes_lesser']:
        boxplot_data.append(data['bugfixes_lesser'])
        labels.append('Low-popularity')
    
    if data['bugfixes_medium']:
        boxplot_data.append(data['bugfixes_medium'])
        labels.append('Medium-popularity')
    
    if data['bugfixes_high']:
        boxplot_data.append(data['bugfixes_high'])
        labels.append('High-popularity')

    if not boxplot_data:
        print("No data available for boxplot creation.")
        return data
    
    # Create the boxplot
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    
    # Create boxplot
    box_parts = ax.boxplot(boxplot_data, labels=labels, patch_artist=True, 
                          notch=True, showmeans=True)
    
    # Customize colors
    for patch, color in zip(box_parts['boxes'], colors[:len(boxplot_data)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Customize the plot
    # ax.set_title('Bugfix Recommendations by Project Quality Categories', fontsize=16, fontweight='bold')
    ax.set_xlabel('Project Quality Category', fontsize=14)
    ax.set_ylabel('Number of Bugfix Recommendations', fontsize=14)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add statistics annotations
    for i, (category_data, label) in enumerate(zip(boxplot_data, labels)):
        if category_data:
            mean_val = sum(category_data) / len(category_data)
            median_val = statistics.median(category_data)
            stats_text = f'n={len(category_data)}\nMean: {mean_val:.2f}\nMedian: {median_val:.2f}'
            
            # Position the text box above each boxplot
            ax.text(i + 1, max(category_data) + 0.5, stats_text, 
                   horizontalalignment='center', fontsize=12,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Adjust layout
    plt.tight_layout()
    
    # Generate filename if no save_path provided
    if save_path is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"bugfix_boxplot_{timestamp}.pdf"
    
    # Save the figure
    plt.savefig(save_path, dpi=300, bbox_inches='tight', format='pdf')
    print(f"Bugfix boxplot saved to: {save_path}")
    
    # Display the plot
    plt.show()
    
    # Print summary
    print(f"\nBoxplot Summary:")
    for i, (category_data, label) in enumerate(zip(boxplot_data, labels)):
        if category_data:
            print(f"  {label.replace(chr(10), ' ')}: {len(category_data)} projects, "
                  f"Mean: {sum(category_data)/len(category_data):.2f}, "
                  f"Median: {statistics.median(category_data):.2f}")
    
    return data

def stat_test(projects_with_codelines_csv_path):
    """
    Perform statistical tests on bugfix and improving code recommendations grouped by project categories.
    
    This function:
    1. Gets bugfix and improving code recommendation data
    2. Performs Shapiro-Wilk normality tests on each group for both datasets
    3. Performs Kruskal-Wallis tests to compare the three groups for both datasets
    
    Args:
        projects_with_codelines_csv_path (str): Path to the projects_with_codelines.csv file
        
    Returns:
        dict: Dictionary containing test results and statistics for both datasets
    """
    print("=" * 80)
    print("STATISTICAL ANALYSIS OF BUGFIX AND IMPROVING CODE RECOMMENDATIONS")
    print("=" * 80)
    
    # Get both datasets using the existing functions
    print("Getting bugfix recommendation data...")
    bugfix_data = bugfix_recommendations_by_groups(projects_with_codelines_csv_path)
    
    print("\nGetting improving code recommendation data...")
    improvingcode_data = improving_code_recommendations_by_groups(projects_with_codelines_csv_path)
    
    # Combine results dictionary
    results = {
        'bugfix_data': bugfix_data,
        'improvingcode_data': improvingcode_data,
        'bugfix_normality_tests': {},
        'improvingcode_normality_tests': {},
        'bugfix_kruskal_wallis': {},
        'improvingcode_kruskal_wallis': {}
    }
    
    # Analyze both datasets
    datasets = [
        ('BUGFIX', bugfix_data, 'bugfixes', 'bugfix_normality_tests', 'bugfix_kruskal_wallis'),
        ('IMPROVING CODE', improvingcode_data, 'improvingcode', 'improvingcode_normality_tests', 'improvingcode_kruskal_wallis')
    ]
    
    for dataset_name, data_dict, prefix, normality_key, kruskal_key in datasets:
        print(f"\n{'=' * 80}")
        print(f"{dataset_name} RECOMMENDATIONS ANALYSIS")
        print(f"{'=' * 80}")
        
        # Extract the three groups
        lesser_group = data_dict[f'{prefix}_lesser']
        medium_group = data_dict[f'{prefix}_medium'] 
        high_group = data_dict[f'{prefix}_high']
        
        print(f"\n{'=' * 60}")
        print(f"NORMALITY TESTS (Shapiro-Wilk) - {dataset_name}")
        print(f"{'=' * 60}")
        
        # Perform Shapiro-Wilk normality tests
        normality_results = {}
        
        groups = [
            ('Lesser-quality', lesser_group),
            ('Medium-quality', medium_group),
            ('High-quality', high_group)
        ]
        
        for group_name, group_data in groups:
            if len(group_data) >= 3:  # Shapiro-Wilk requires at least 3 samples
                try:
                    statistic, p_value = stats.shapiro(group_data)
                    normality_results[group_name] = {
                        'statistic': statistic,
                        'p_value': p_value,
                        'is_normal': p_value > 0.05,
                        'n': len(group_data)
                    }
                    
                    print(f"\n{group_name} Projects:")
                    print(f"  Sample size: {len(group_data)}")
                    print(f"  Shapiro-Wilk statistic: {statistic:.6f}")
                    print(f"  P-value: {p_value:.6f}")
                    print(f"  Normal distribution: {'Yes' if p_value > 0.05 else 'No'} (α = 0.05)")
                    
                except Exception as e:
                    print(f"\n{group_name} Projects:")
                    print(f"  Error performing Shapiro-Wilk test: {e}")
                    normality_results[group_name] = {'error': str(e)}
            else:
                print(f"\n{group_name} Projects:")
                print(f"  Sample size too small for Shapiro-Wilk test: {len(group_data)} (minimum 3 required)")
                normality_results[group_name] = {'error': 'Sample size too small'}
        
        results[normality_key] = normality_results
        
        print(f"\n{'=' * 60}")
        print(f"KRUSKAL-WALLIS TEST - {dataset_name}")
        print(f"{'=' * 60}")
        
        # Prepare groups for Kruskal-Wallis test (only include non-empty groups)
        kruskal_groups = []
        group_names = []
        
        if lesser_group:
            kruskal_groups.append(lesser_group)
            group_names.append('Lesser-quality')
        
        if medium_group:
            kruskal_groups.append(medium_group)
            group_names.append('Medium-quality')
            
        if high_group:
            kruskal_groups.append(high_group)
            group_names.append('High-quality')
        
        kruskal_results = {}
        
        if len(kruskal_groups) >= 2:  # Need at least 2 groups for comparison
            try:
                statistic, p_value = stats.kruskal(*kruskal_groups)
                kruskal_results = {
                    'statistic': statistic,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'groups_compared': group_names,
                    'degrees_of_freedom': len(kruskal_groups) - 1
                }
                
                print(f"Comparing groups: {', '.join(group_names)}")
                print(f"Kruskal-Wallis statistic (H): {statistic:.6f}")
                print(f"P-value: {p_value:.6f}")
                print(f"Degrees of freedom: {len(kruskal_groups) - 1}")
                print(f"Significant difference: {'Yes' if p_value < 0.05 else 'No'} (α = 0.05)")
                
                if p_value < 0.05:
                    print(f"\nInterpretation: There is a statistically significant difference")
                    print(f"between the {dataset_name.lower()} recommendations across project quality groups.")
                else:
                    print(f"\nInterpretation: There is no statistically significant difference")
                    print(f"between the {dataset_name.lower()} recommendations across project quality groups.")
                    
            except Exception as e:
                print(f"Error performing Kruskal-Wallis test: {e}")
                kruskal_results = {'error': str(e)}
        else:
            print("Cannot perform Kruskal-Wallis test: Need at least 2 non-empty groups")
            kruskal_results = {'error': 'Insufficient groups for comparison'}
        
        results[kruskal_key] = kruskal_results
        
        print(f"\n{'=' * 60}")
        print(f"SUMMARY STATISTICS - {dataset_name}")
        print(f"{'=' * 60}")
        
        for group_name, group_data in groups:
            if group_data:
                print(f"\n{group_name} Projects:")
                print(f"  Count: {len(group_data)}")
                print(f"  Mean: {statistics.mean(group_data):.4f}")
                print(f"  Median: {statistics.median(group_data):.4f}")
                print(f"  Std Dev: {statistics.stdev(group_data):.4f}" if len(group_data) > 1 else "  Std Dev: N/A (single value)")
                print(f"  Min: {min(group_data):.4f}")
                print(f"  Max: {max(group_data):.4f}")
    
    # Add overall summary
    print(f"\n{'=' * 80}")
    print("OVERALL COMPARISON SUMMARY")
    print(f"{'=' * 80}")
    
    # Compare Kruskal-Wallis results
    bugfix_significant = results['bugfix_kruskal_wallis'].get('significant', False)
    improvingcode_significant = results['improvingcode_kruskal_wallis'].get('significant', False)
    
    print(f"\nKruskal-Wallis Test Results:")
    print(f"  Bugfix recommendations: {'Significant' if bugfix_significant else 'Not significant'}")
    print(f"  Improving code recommendations: {'Significant' if improvingcode_significant else 'Not significant'}")
    
    if bugfix_significant and improvingcode_significant:
        print(f"\nBoth recommendation types show significant differences across project quality groups.")
    elif bugfix_significant or improvingcode_significant:
        significant_type = "Bugfix" if bugfix_significant else "Improving code"
        print(f"\nOnly {significant_type.lower()} recommendations show significant differences across project quality groups.")
    else:
        print(f"\nNeither recommendation type shows significant differences across project quality groups.")
    
    # Add summary statistics
    results['summary'] = {
        'bugfix_total_projects': sum(len(group_data) for _, group_data in [
            ('lesser', bugfix_data['bugfixes_lesser']),
            ('medium', bugfix_data['bugfixes_medium']),
            ('high', bugfix_data['bugfixes_high'])
        ]),
        'improvingcode_total_projects': sum(len(group_data) for _, group_data in [
            ('lesser', improvingcode_data['improvingcode_lesser']),
            ('medium', improvingcode_data['improvingcode_medium']),
            ('high', improvingcode_data['improvingcode_high'])
        ]),
        'bugfix_groups_with_data': len([g for g in [
            bugfix_data['bugfixes_lesser'],
            bugfix_data['bugfixes_medium'],
            bugfix_data['bugfixes_high']
        ] if g]),
        'improvingcode_groups_with_data': len([g for g in [
            improvingcode_data['improvingcode_lesser'],
            improvingcode_data['improvingcode_medium'],
            improvingcode_data['improvingcode_high']
        ] if g])
    }
    
    return results

def improving_code_vs_gh_groups(improving_code_csv_path, save_path=None):
    """
    Read the improving_code.csv file and plot a black and white horizontal bar chart showing 
    the count and percentage of values in the matcha_subtype column, grouped by the group column.
    Uses different hatching patterns to distinguish between the bars.
    
    Args:
        improving_code_csv_path (str): Path to the improving_code.csv file
        save_path (str, optional): Path to save the figure. If None, uses default naming.
        
    Returns:
        dict: Dictionary containing:
            - 'counts': Dictionary with the counts of each matcha_subtype grouped by group
            - 'percentages': Dictionary with the percentage of each matcha_subtype within its group
            - 'group_totals': Dictionary with the total counts for each group
    """
    # Convert to Path object
    csv_path = Path(improving_code_csv_path)
    
    # Validate input file
    if not csv_path.exists():
        raise ValueError(f"CSV file {improving_code_csv_path} does not exist")
    
    # Dictionary to store counts: {group: {subtype: count}}
    group_subtype_counts = {}
    
    # Read the CSV and count occurrences
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                group = row.get('group', '').strip()
                subtype = row.get('matcha_subtype', '').strip()
                
                if group and subtype:
                    if group not in group_subtype_counts:
                        group_subtype_counts[group] = {}
                    
                    if subtype not in group_subtype_counts[group]:
                        group_subtype_counts[group][subtype] = 0
                    
                    group_subtype_counts[group][subtype] += 1
    
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}") from e
    
    # Get all unique subtypes across all groups
    all_subtypes = set()
    for group_data in group_subtype_counts.values():
        all_subtypes.update(group_data.keys())
    all_subtypes = sorted(list(all_subtypes))
    
    # Get all groups and sort them
    all_groups = sorted(group_subtype_counts.keys())
    
    # Calculate total counts for each group
    group_totals = {}
    for group in all_groups:
        group_totals[group] = sum(group_subtype_counts[group].values())
    
    # Calculate percentages
    group_subtype_percentages = {}
    for group in all_groups:
        group_subtype_percentages[group] = {}
        total = group_totals[group]
        if total > 0:  # Avoid division by zero
            for subtype in all_subtypes:
                count = group_subtype_counts[group].get(subtype, 0)
                percentage = (count / total) * 100 if total > 0 else 0
                group_subtype_percentages[group][subtype] = percentage
    
    # Print summary with counts and percentages
    print("Improving Code Recommendations by Group and Subtype:")
    for group in all_groups:
        print(f"\nGroup {group} (Total: {group_totals[group]}):")
        for subtype in all_subtypes:
            count = group_subtype_counts[group].get(subtype, 0)
            percentage = group_subtype_percentages[group].get(subtype, 0)
            print(f"  {subtype}: {count} ({percentage:.2f}%)")
    
    # Create data for plotting
    # For each subtype, create a list of counts across all groups
    subtype_data = {}
    subtype_percentages = {}
    for subtype in all_subtypes:
        subtype_data[subtype] = [group_subtype_counts.get(group, {}).get(subtype, 0) for group in all_groups]
        subtype_percentages[subtype] = [group_subtype_percentages.get(group, {}).get(subtype, 0) for group in all_groups]
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Position for bars
    bar_positions = range(len(all_groups))
    bar_width = 0.8 / len(all_subtypes)
    
    # Define patterns for black and white theme
    # List of patterns: '/', '\', '|', '-', '+', 'x', 'o', 'O', '.', '*'
    patterns = ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']
    legend_patches = []
    
    for i, (subtype, counts) in enumerate(subtype_data.items()):
        positions = [pos + i * bar_width for pos in bar_positions]
        # Use black edgecolor and white facecolor with hatching pattern
        bars = ax.barh(positions, counts, bar_width, label=subtype, 
                      edgecolor='black', facecolor='white', 
                      hatch=patterns[i % len(patterns)], alpha=0.9)
        
        # Add data labels to bars with both count and percentage
        for j, (bar, count) in enumerate(zip(bars, counts)):
            if count > 0:  # Only add label if count > 0
                percentage = subtype_percentages[subtype][j]
                label_text = f"{count} ({percentage:.1f}%)"
                ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, 
                        label_text, ha='left', va='center', fontsize=9)
        
        # Add to legend with the same pattern
        patch = plt.Rectangle((0, 0), 1, 1, 
                             edgecolor='black', facecolor='white', 
                             hatch=patterns[i % len(patterns)])
        legend_patches.append(patch)
    
    # Set chart title and labels
    # ax.set_title('Improving Code Recommendations by Group and Subtype', fontsize=14, fontweight='bold')
    ax.set_xlabel('Count', fontsize=14)
    # ax.set_ylabel('Group', fontsize=14)
    
    # Set y-ticks
    y_positions = [pos + (len(all_subtypes) - 1) * bar_width / 2 for pos in bar_positions]
    ax.set_yticks(y_positions)
    ax.set_yticklabels(['High-quality', 'Medium-quality', 'Low-quality'], fontsize=12)
    
    # Add legend with black & white style
    legend = ax.legend(legend_patches, all_subtypes, loc='upper right', fontsize=10,
                      frameon=True, facecolor='white', edgecolor='black')
    
    # Add grid lines (gray for black and white theme)
    ax.grid(True, axis='x', linestyle='--', color='gray', alpha=0.5)
    
    # Adjust layout
    plt.tight_layout()
    
    # Generate filename if no save_path provided
    if save_path is None:
        save_path = "improving_code_vs_gh_groups.pdf"
    
    # Save the figure
    plt.savefig(save_path, dpi=300, bbox_inches='tight', format='pdf')
    print(f"Horizontal bar chart saved to: {save_path}")
    
    # Display the plot
    plt.show()
    
    # Return both counts and percentages
    return {
        'counts': group_subtype_counts,
        'percentages': group_subtype_percentages,
        'group_totals': group_totals
    }


# Example usage
if __name__ == "__main__":
    # Example: count_code_lines("/Users/chaiyong/Downloads/do_not_delete/Matcha Study/GHProjects")
    # Example: map_lines_to_project("projects.csv", "code_lines_count.csv")
    # Example: group_lines_by_categories("projects_with_codelines.csv")
    # Example: draw_code_size_histograms("projects_with_codelines.csv")
    # Example: bugfix_recommendations_by_groups("projects_with_codelines.csv")
    print("Available functions:")
    print("1. count_code_lines(directory_path) - Count lines of code in subdirectories")
    print("2. map_lines_to_project(projects_csv, codelines_csv) - Map code lines to projects")
    print("3. group_lines_by_categories(projects_with_codelines_csv) - Group code lines by region categories")
    print("4. draw_code_size_histograms(projects_with_codelines_csv) - Create histograms of code sizes")
    print("5. bugfix_recommendations_by_groups(projects_with_codelines_csv) - Group bugfix recommendations by categories")
    print("6. improving_code_recommendations_by_groups(projects_with_codelines_csv) - Group improving code recommendations by categories")
    print("7. draw_bugfix_boxplots(projects_with_codelines_csv) - Create boxplots of bugfix recommendations")
    print("8. stat_test(projects_with_codelines_csv) - Perform statistical tests on bugfix recommendations")
    print("9. improving_code_vs_gh_groups(improving_code_csv) - Plot horizontal bar chart of matcha_subtype counts by group")
    
    # count_code_lines("/Users/chaiyong/Downloads/do_not_delete/Matcha Study/GHProjects", "code_lines_count.csv")
    # map_lines_to_project("GH_selection_revise_FIXED.csv", "code_lines_count.csv")
    
    # Example: Group projects by categories and create histograms
    # result = group_lines_by_categories("projects_with_codelines.csv")
    # print("\nCode lines data:")
    # print(f"Lesser projects: {len(result['lesser'])} entries")
    # print(f"Medium projects: {len(result['medium'])} entries") 
    # print(f"High projects: {len(result['high'])} entries")
    
    # # Create histograms
    # print("\nCreating histograms...")
    # draw_code_size_histograms("/Users/chaiyong/Downloads/do_not_delete/Matcha_Study/SOPostProcessor/analysis/projects_with_codelines.csv")
    
    # # Example: Group bugfix recommendations by categories
    # print("\nGrouping bugfix recommendations...")
    # bugfix_result = bugfix_recommendations_by_groups("projects_with_codelines.csv")
    # print(f"\nBugfix recommendations data:")
    # print(f"Lesser category: {len(bugfix_result['bugfixes_lesser'])} entries")
    # print(f"Medium category: {len(bugfix_result['bugfixes_medium'])} entries")
    # print(f"High category: {len(bugfix_result['bugfixes_high'])} entries")

    # improving_result = improving_code_recommendations_by_groups("projects_with_codelines.csv")

    # # Create bugfix boxplots
    # # print("\nCreating bugfix boxplots...")
    # draw_bugfix_boxplots("/Users/chaiyong/Downloads/do_not_delete/Matcha_Study/SOPostProcessor/analysis/projects_with_codelines.csv")
    # stat_test("projects_with_codelines.csv")
    
    # Example: Create horizontal bar chart for improving code vs github groups
    # improving_code_vs_gh_groups("/Users/chaiyong/Downloads/do_not_delete/Matcha_Study/SOPostProcessor/analysis/improving_code.csv")

    