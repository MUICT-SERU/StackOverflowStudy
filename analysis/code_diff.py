#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Diff Analysis Tool

This script provides utilities for finding and comparing Java code files.
It can find pairs of files with matching prefixes and compute edit distances between them.

Dependencies:
    - python-Levenshtein (optional): For faster edit distance calculation
      Install with: pip install python-Levenshtein
    - matplotlib (optional): For generating visualization plots
      Install with: pip install matplotlib
"""

import os
import csv
import math
from typing import List, Tuple, Dict

# Try to import matplotlib for visualization
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: Matplotlib library not found. Visualization features will be disabled.")
    print("To install, run: pip install matplotlib")

try:
    import Levenshtein
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False
    print("Warning: Python-Levenshtein library not found. Using built-in implementation.")
    print("To install, run: pip install python-Levenshtein")


def get_all_folders(path: str) -> List[str]:
    """
    Read a given path and return a list of folders in that path.

    Args:
        path: A string representing the directory path to search in.

    Returns:
        A list of strings containing the names of all folders (not files) in the specified path.
        Returns an empty list if the path doesn't exist or contains no folders.

    Example:
        >>> get_all_folders('/path/to/directory')
        ['folder1', 'folder2', 'folder3']
    """
    folders = []
    
    # Check if the path exists and is a directory
    if os.path.exists(path) and os.path.isdir(path):
        # List all items in the directory
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            # Check if the item is a directory (folder)
            if os.path.isdir(item_path):
                folders.append(item)
    
    return folders


def compute_distance(file_path1: str, file_path2: str) -> int:
    """
    Compute the Levenshtein edit distance between two code snippets
    by reading the code from the given file paths.
    
    Uses python-Levenshtein library if available, otherwise falls back
    to a built-in implementation.
    
    Args:
        file_path1: Path to the first file.
        file_path2: Path to the second file.
        
    Returns:
        An integer representing the Levenshtein distance between the two code snippets.
        Returns -1 if either file cannot be read.
        
    Example:
        >>> compute_distance('/path/to/file1.java', '/path/to/file2.java')
        42
    """
    # Try to read the content of both files
    try:
        with open(file_path1, 'r', encoding='utf-8') as f1:
            code1 = f1.read()
    except (IOError, OSError, UnicodeDecodeError) as e:
        print(f"Error reading file {file_path1}: {e}")
        return -1
        
    try:
        with open(file_path2, 'r', encoding='utf-8') as f2:
            code2 = f2.read()
    except (IOError, OSError, UnicodeDecodeError) as e:
        print(f"Error reading file {file_path2}: {e}")
        return -1
    
    # Use python-Levenshtein library if available, otherwise use built-in implementation
    if LEVENSHTEIN_AVAILABLE:
        return Levenshtein.distance(code1, code2)
    else:
        return levenshtein_distance(code1, code2)


def read_distances_from_csv(csv_path: str) -> List[int]:
    """
    Read Levenshtein distances from a CSV file.
    
    Args:
        csv_path: Path to the CSV file containing Levenshtein distances
        
    Returns:
        A list of distance values
        Returns an empty list if the file doesn't exist or cannot be read
        
    Example:
        >>> read_distances_from_csv('levenshtein_distances.csv')
        [42, 17, 56, 23, 89, 12, 45]
    """
    distances = []
    
    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return []
        
    try:
        # Read distances from CSV file
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip header row
            for row in csv_reader:
                if len(row) >= 3:  # Ensure there are at least 3 columns
                    try:
                        dist_value = int(row[2])  # Distance is in the third column
                        distances.append(dist_value)
                    except ValueError:
                        print(f"Warning: Could not convert '{row[2]}' to integer, skipping row")
    except (IOError, OSError) as e:
        print(f"Error reading CSV file: {e}")
        return []
        
    # If no valid distances were found, return empty list
    if not distances:
        print("No valid distances found in the CSV file")
    
    return distances


def analyze_levenshtein_distances(csv_path: str = None, distances: List[int] = None) -> Dict[str, float]:
    """
    Analyze Levenshtein distances to provide statistical measures.
    
    Args:
        csv_path: Path to the CSV file containing Levenshtein distances (optional)
                 If provided, distances will be read from this file
        distances: List of distance values (optional)
                  If provided, these values will be analyzed directly
                  
    Note:
        Either csv_path or distances must be provided.
        If both are provided, distances parameter takes precedence.
        
    Returns:
        A dictionary with statistical measures: min, max, mean, median, standard deviation, count
        Returns empty dictionary if no valid distances are available
        
    Example:
        >>> analyze_levenshtein_distances('levenshtein_distances.csv')
        {'min': 5, 'max': 120, 'mean': 45.7, 'median': 42.0, 'std_dev': 28.3, 'count': 10}
        >>> analyze_levenshtein_distances(distances=[42, 17, 56, 23, 89, 12, 45])
        {'min': 12, 'max': 89, 'mean': 40.57, 'median': 42.0, 'std_dev': 25.73, 'count': 7}
    """
    # Determine the source of distances
    if distances is None and csv_path is None:
        print("Error: Either csv_path or distances must be provided")
        return {}
    
    # If distances not provided but csv_path is, read from CSV
    if distances is None:
        distances = read_distances_from_csv(csv_path)
    
    # If no valid distances available, return empty results
    if not distances:
        return {}
    
    # Calculate statistics
    count = len(distances)
    min_dist = min(distances)
    max_dist = max(distances)
    mean = sum(distances) / count
    
    # Calculate median
    sorted_distances = sorted(distances)
    mid = count // 2
    if count % 2 == 0:
        median = (sorted_distances[mid - 1] + sorted_distances[mid]) / 2
    else:
        median = sorted_distances[mid]
    
    # Calculate standard deviation
    variance = sum((x - mean) ** 2 for x in distances) / count
    std_dev = math.sqrt(variance)
    
    # Round floating point values for readability
    return {
        'min': min_dist,
        'max': max_dist,
        'mean': round(mean, 2),
        'median': round(median, 2),
        'std_dev': round(std_dev, 2),
        'count': count,
        'raw_distances': distances  # Include raw distances for boxplot
    }


def generate_boxplot(distances: List[int], output_path: str = None) -> bool:
    """
    Generate a horizontal boxplot visualization of the Levenshtein distances.
    
    Args:
        distances: A list of Levenshtein distance values
        output_path: Path to save the boxplot image (optional)
                     If not provided, the plot will be displayed but not saved.
                     The function saves both PNG and PDF formats.
                     
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> distances = [42, 17, 56, 23, 89, 12, 45]
        >>> generate_boxplot(distances, 'levenshtein_boxplot.png')
        # Saves both levenshtein_boxplot.png and levenshtein_boxplot.pdf
        True
    """
    # Check if matplotlib is available
    if not MATPLOTLIB_AVAILABLE:
        print("Cannot generate boxplot: Matplotlib library is not available")
        return False
        
    # Check if there are any distances to plot
    if not distances:
        print("Cannot generate boxplot: No distances provided")
        return False
    
    try:
        # Create a new figure with a specific size
        plt.figure(figsize=(10, 3))
        
        # Create a horizontal boxplot with the distances (vert=False makes it horizontal)
        boxplot = plt.boxplot(distances, patch_artist=True, vert=False)
        
        # Customize boxplot colors
        for box in boxplot['boxes']:
            box.set(facecolor='lightblue', edgecolor='blue', linewidth=2)
        for whisker in boxplot['whiskers']:
            whisker.set(color='blue', linewidth=2)
        for cap in boxplot['caps']:
            cap.set(color='blue', linewidth=2)
        for median in boxplot['medians']:
            median.set(color='red', linewidth=2)
        for flier in boxplot['fliers']:
            flier.set(marker='o', markerfacecolor='red', markersize=5, 
                    markeredgecolor='black', alpha=0.5)
        
        # Add title and labels
        plt.title('Levenshtein Distance Distribution (Horizontal)', fontsize=16)
        plt.xlabel('Levenshtein distance', fontsize=14)  # X-axis now represents distance values
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Remove y-tick labels as they're not meaningful in a single boxplot
        plt.yticks([])
        
        # # Add statistical annotations
        # stats_text = (
        #     f"n = {len(distances)}\n"
        #     f"Min: {min(distances)}\n"
        #     f"Max: {max(distances)}\n"
        #     f"Mean: {sum(distances) / len(distances):.2f}\n"
        #     f"Median: {sorted(distances)[len(distances) // 2]}"
        # )
        # plt.annotate(stats_text, xy=(0.02, 0.95), xycoords='figure fraction', 
        #             fontsize=12, bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8))
        
        # Save the figure if a path is provided
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Horizontal boxplot saved to: {output_path}")
            
            # Save as PDF (replace extension or add .pdf if no extension)
            pdf_path = os.path.splitext(output_path)[0] + '.pdf'
            plt.savefig(pdf_path, format='pdf', bbox_inches='tight')
            print(f"Horizontal boxplot saved as PDF: {pdf_path}")
        
        # Show the plot (this will display the plot in a new window)
        plt.tight_layout()
        plt.show()
        
        return True
    except Exception as e:
        print(f"Error generating boxplot: {e}")
        return False


def save_distances_to_csv(distances: List[Tuple[str, str, int]], output_path: str) -> bool:
    """
    Save the Levenshtein distances to a CSV file.
    
    Args:
        distances: A list of tuples containing (file_path1, file_path2, distance)
        output_path: Path to the output CSV file
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> distances = [
        ...     ('/path/to/file1.java', '/path/to/file2.java', 42),
        ...     ('/path/to/file3.java', '/path/to/file4.java', 17)
        ... ]
        >>> save_distances_to_csv(distances, 'distances.csv')
        True
    """
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write the header
            csv_writer.writerow(['First File', 'Second File', 'Levenshtein Distance'])
            # Write the data rows
            for file1, file2, dist_value in distances:
                csv_writer.writerow([file1, file2, dist_value])
        return True
    except (IOError, OSError, ValueError) as e:
        print(f"Error saving CSV file: {e}")
        return False


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    This is a fallback implementation used when python-Levenshtein is not available.
    
    Args:
        s1: First string.
        s2: Second string.
        
    Returns:
        The Levenshtein distance between the two strings.
    """
    # Create a matrix of size (len(s1)+1) x (len(s2)+1)
    rows = len(s1) + 1
    cols = len(s2) + 1
    
    # Initialize the matrix with default values
    matrix = [[0 for _ in range(cols)] for _ in range(rows)]
    
    # Initialize the first row and column with incremental values
    for row in range(rows):
        matrix[row][0] = row
    for col in range(cols):
        matrix[0][col] = col
    
    # Fill the matrix using dynamic programming
    for row in range(1, rows):
        for col in range(1, cols):
            if s1[row-1] == s2[col-1]:
                # Characters match, no operation needed
                cost = 0
            else:
                # Characters don't match, need a substitution
                cost = 1
            
            # Minimum of deletion, insertion, substitution
            matrix[row][col] = min(
                matrix[row-1][col] + 1,       # Deletion
                matrix[row][col-1] + 1,       # Insertion
                matrix[row-1][col-1] + cost   # Substitution
            )
    
    # The bottom-right cell contains the Levenshtein distance
    return matrix[rows-1][cols-1]


def get_answer_version_pair(path: str) -> List[Tuple[str, str]]:
    """
    Find all pairs of files in the given path that share the same prefix, where
    one file ends with '_original.java' and the other with '_recent.java'.

    Args:
        path: A string representing the directory path to search in.
        
    Returns:
        A list of tuples, where each tuple contains two file paths (original_file, recent_file).
        Returns an empty list if no matching pairs are found or the path doesn't exist.
        
    Example:
        >>> get_answer_version_pair('/path/to/files')
        [
            ('/path/to/files/answer1_original.java', '/path/to/files/answer1_recent.java'),
            ('/path/to/files/answer2_original.java', '/path/to/files/answer2_recent.java')
        ]
    """
    # List to store all matching pairs
    matching_pairs = []
    
    # Check if the path exists and is a directory
    if not os.path.exists(path) or not os.path.isdir(path):
        return matching_pairs
    
    # Dictionary to store files by their prefix
    file_dict = {
        'original': {},  # Will store original files with prefix as key
        'recent': {}     # Will store recent files with prefix as key
    }
    
    # Get all files in the directory
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        
        # Only process regular files
        if os.path.isfile(item_path):
            # Check if the file ends with _original.java
            if item.endswith('_original.java'):
                # Extract the prefix (everything before _original.java)
                prefix = item[:-14]  # Remove '_original.java'
                file_dict['original'][prefix] = item_path
            
            # Check if the file ends with _recent.java
            elif item.endswith('_recent.java'):
                # Extract the prefix (everything before _recent.java)
                prefix = item[:-12]  # Remove '_recent.java'
                file_dict['recent'][prefix] = item_path
    
    # Look for matching pairs (same prefix)
    for prefix in file_dict['original']:
        if prefix in file_dict['recent']:
            # Found a matching pair, add it to our list
            matching_pairs.append((file_dict['original'][prefix], file_dict['recent'][prefix]))
    
    # Return all matching pairs
    return matching_pairs


def find_and_compute_distances(base_path: str) -> List[Tuple[str, str, int]]:
    """
    Find all original-recent file pairs in the given path and compute
    Levenshtein distances between them.
    
    Args:
        base_path: Base directory path to search in.
        
    Returns:
        A list of tuples containing (file_path1, file_path2, distance).
    """
    # Get all folders in the base path
    all_folders = get_all_folders(base_path)
    print(f"Found {len(all_folders)} folders in {base_path}")
    
    # List to store all distance records
    all_distances = []
    total_pairs_found = 0
    
    # Loop through each folder and find file pairs
    print("\nLooking for original-recent file pairs in all subfolders:")
    
    for folder in all_folders:
        # Create the full path to the subfolder
        folder_path = os.path.join(base_path, folder)
        print(f"\nExamining folder: {folder}")
        
        # Call get_answer_version_pair for each folder
        file_pairs = get_answer_version_pair(folder_path)
        
        if file_pairs:
            folder_pairs_count = len(file_pairs)
            total_pairs_found += folder_pairs_count
            print(f"Found {folder_pairs_count} matching pair(s):")
            
            # Process each pair
            for i, (original_file, recent_file) in enumerate(file_pairs, 1):
                print(f"  Pair {i}:")
                print(f"    Original: {os.path.basename(original_file)}")
                print(f"    Recent: {os.path.basename(recent_file)}")
                
                # Compute the Levenshtein distance
                distance = compute_distance(original_file, recent_file)
                if distance >= 0:
                    method = "python-Levenshtein" if LEVENSHTEIN_AVAILABLE else "built-in algorithm"
                    print(f"    Edit Distance: {distance} (using {method})")
                    
                    # Add to our list of distances
                    all_distances.append((original_file, recent_file, distance))
                else:
                    print("    Edit Distance: Error computing distance")
        else:
            print("No matching file pairs found in this folder.")
    
    print(f"\nTotal pairs found across all folders: {total_pairs_found}")
    return all_distances


def print_statistics(stats: Dict) -> None:
    """
    Print the statistical analysis results.
    
    Args:
        stats: Dictionary containing statistical measures.
    """
    if not stats:
        print("No statistics available.")
        return
        
    print("\nStatistical Analysis Results:")
    print(f"  Number of pairs analyzed: {stats['count']}")
    print(f"  Minimum distance: {stats['min']}")
    print(f"  Maximum distance: {stats['max']}")
    print(f"  Mean distance: {stats['mean']}")
    print(f"  Median distance: {stats['median']}")
    print(f"  Standard deviation: {stats['std_dev']}")


if __name__ == "__main__":
    # Example usage
    import sys
    import os.path
    
    # Step 1: Determine input path and output paths
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    else:
        test_path = "/Users/chaiyong/Downloads/do_not_delete/Matcha_Study/java_files"
    
    # Define output files
    output_dir = os.path.dirname(test_path)
    output_csv = os.path.join(output_dir, "levenshtein_distances.csv")
    boxplot_path = os.path.join(output_dir, "levenshtein_boxplot.png")
    
    # # Step 2: Find file pairs and compute distances
    # print("\n=== STEP 1: Finding file pairs and computing distances ===")
    # all_distances = find_and_compute_distances(test_path)
    
    # if not all_distances:
    #     print("\nNo distances were computed. Exiting.")
    #     sys.exit(0)
    
    # # Step 3: Save distances to CSV file
    # print("\n=== STEP 2: Saving distances to CSV file ===")
    # if save_distances_to_csv(all_distances, output_csv):
    #     print(f"Levenshtein distances saved to: {output_csv}")
    # else:
    #     print("Failed to save distances to CSV file.")
    #     sys.exit(1)
    
    # Step 4: Read distances from CSV
    print("\n=== STEP 3: Reading distances from CSV ===")
    distances = read_distances_from_csv(output_csv)
    if not distances:
        print("No valid distances found. Exiting.")
        sys.exit(1)
    print(f"Successfully read {len(distances)} distance values from CSV.")
    
    # Step 5: Analyze the distances and print statistics
    print("\n=== STEP 4: Analyzing distances ===")
    stats = analyze_levenshtein_distances(distances=distances)
    print_statistics(stats)
    
    # Step 6: Generate visualizations (PNG and PDF)
    print("\n=== STEP 5: Generating visualizations ===")
    if distances:
        print("Generating boxplot visualizations (PNG and PDF)...")
        pdf_path = os.path.splitext(boxplot_path)[0] + '.pdf'
        if generate_boxplot(distances, boxplot_path):
            # The function itself now prints the output paths
            pass
        else:
            print("Failed to generate boxplot visualizations.")
    else:
        print("No valid distance data available for visualization.")
