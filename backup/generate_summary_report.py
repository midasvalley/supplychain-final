import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def generate_summary_report():
    """
    Generate a comprehensive summary report of all the changes made to the nutrition data.
    """
    # Load the original and final data
    try:
        original_df = pd.read_csv('usda_nutrition_data.csv')
        print(f"Loaded original data with {len(original_df)} rows")
        
        final_df = pd.read_csv('usda_nutrition_data_final_complete.csv')
        print(f"Loaded final data with {len(final_df)} rows")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return
    
    # Create a report file
    report_filename = 'nutrition_data_improvement_report.txt'
    with open(report_filename, 'w') as report_file:
        # Write report header
        report_file.write("=" * 80 + "\n")
        report_file.write("USDA NUTRITION DATA IMPROVEMENT REPORT\n")
        report_file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_file.write("=" * 80 + "\n\n")
        
        # Write data overview
        report_file.write("DATA OVERVIEW\n")
        report_file.write("-" * 80 + "\n")
        report_file.write(f"Total number of items: {len(original_df)}\n\n")
        
        # Calculate match confidence statistics for original data
        original_threshold = 0.5
        original_low_confidence = original_df[original_df['Match Confidence'] < original_threshold]
        original_high_confidence = original_df[original_df['Match Confidence'] >= original_threshold]
        
        report_file.write("ORIGINAL DATA QUALITY\n")
        report_file.write("-" * 80 + "\n")
        report_file.write(f"Items with match confidence >= {original_threshold}: {len(original_high_confidence)} ({len(original_high_confidence)/len(original_df)*100:.2f}%)\n")
        report_file.write(f"Items with match confidence < {original_threshold}: {len(original_low_confidence)} ({len(original_low_confidence)/len(original_df)*100:.2f}%)\n\n")
        
        # Calculate match confidence statistics for final data
        final_threshold = 0.5
        final_low_confidence = final_df[final_df['Match Confidence'] < final_threshold]
        final_high_confidence = final_df[final_df['Match Confidence'] >= final_threshold]
        
        report_file.write("FINAL DATA QUALITY\n")
        report_file.write("-" * 80 + "\n")
        report_file.write(f"Items with match confidence >= {final_threshold}: {len(final_high_confidence)} ({len(final_high_confidence)/len(final_df)*100:.2f}%)\n")
        report_file.write(f"Items with match confidence < {final_threshold}: {len(final_low_confidence)} ({len(final_low_confidence)/len(final_df)*100:.2f}%)\n\n")
        
        # Calculate improvement
        improvement = len(original_low_confidence) - len(final_low_confidence)
        improvement_percentage = (improvement / len(original_low_confidence)) * 100
        report_file.write("IMPROVEMENT SUMMARY\n")
        report_file.write("-" * 80 + "\n")
        report_file.write(f"Fixed {improvement} out of {len(original_low_confidence)} low confidence matches ({improvement_percentage:.2f}%)\n\n")
        
        # Generate detailed match confidence distribution for final data
        report_file.write("FINAL MATCH CONFIDENCE DISTRIBUTION\n")
        report_file.write("-" * 80 + "\n")
        confidence_ranges = {
            '0.9-1.0': final_df[(final_df['Match Confidence'] >= 0.9) & (final_df['Match Confidence'] <= 1.0)].shape[0],
            '0.8-0.9': final_df[(final_df['Match Confidence'] >= 0.8) & (final_df['Match Confidence'] < 0.9)].shape[0],
            '0.7-0.8': final_df[(final_df['Match Confidence'] >= 0.7) & (final_df['Match Confidence'] < 0.8)].shape[0],
            '0.6-0.7': final_df[(final_df['Match Confidence'] >= 0.6) & (final_df['Match Confidence'] < 0.7)].shape[0],
            '0.5-0.6': final_df[(final_df['Match Confidence'] >= 0.5) & (final_df['Match Confidence'] < 0.6)].shape[0],
            '<0.5': final_df[final_df['Match Confidence'] < 0.5].shape[0]
        }
        
        for range_name, count in confidence_ranges.items():
            percentage = (count / len(final_df)) * 100
            report_file.write(f"Match Confidence {range_name}: {count} items ({percentage:.2f}%)\n")
        report_file.write("\n")
        
        # List all changes made
        changes = []
        for _, original_row in original_df.iterrows():
            uid = original_row['UID']
            final_row = final_df[final_df['UID'] == uid].iloc[0]
            
            if original_row['USDA Name'] != final_row['USDA Name'] or original_row['Match Confidence'] != final_row['Match Confidence']:
                changes.append({
                    'UID': uid,
                    'Amazon Name': original_row['Amazon Name'],
                    'Original USDA Name': original_row['USDA Name'],
                    'Final USDA Name': final_row['USDA Name'],
                    'Original Match Confidence': original_row['Match Confidence'],
                    'Final Match Confidence': final_row['Match Confidence']
                })
        
        report_file.write("DETAILED CHANGES MADE\n")
        report_file.write("-" * 80 + "\n")
        report_file.write(f"Total changes made: {len(changes)}\n\n")
        
        for i, change in enumerate(changes, 1):
            report_file.write(f"Change #{i}:\n")
            report_file.write(f"  UID: {change['UID']}\n")
            report_file.write(f"  Amazon Name: {change['Amazon Name']}\n")
            report_file.write(f"  Original USDA Name: {change['Original USDA Name']}\n")
            report_file.write(f"  Final USDA Name: {change['Final USDA Name']}\n")
            report_file.write(f"  Original Match Confidence: {change['Original Match Confidence']}\n")
            report_file.write(f"  Final Match Confidence: {change['Final Match Confidence']}\n")
            report_file.write(f"  Confidence Improvement: {change['Final Match Confidence'] - change['Original Match Confidence']:.4f}\n")
            report_file.write("\n")
    
    print(f"Generated summary report: {report_filename}")
    
    # Create visualizations
    try:
        # Create a bar chart comparing original vs final match confidence distribution
        plt.figure(figsize=(12, 6))
        
        # Original data distribution
        original_ranges = {
            '0.9-1.0': original_df[(original_df['Match Confidence'] >= 0.9) & (original_df['Match Confidence'] <= 1.0)].shape[0],
            '0.8-0.9': original_df[(original_df['Match Confidence'] >= 0.8) & (original_df['Match Confidence'] < 0.9)].shape[0],
            '0.7-0.8': original_df[(original_df['Match Confidence'] >= 0.7) & (original_df['Match Confidence'] < 0.8)].shape[0],
            '0.6-0.7': original_df[(original_df['Match Confidence'] >= 0.6) & (original_df['Match Confidence'] < 0.7)].shape[0],
            '0.5-0.6': original_df[(original_df['Match Confidence'] >= 0.5) & (original_df['Match Confidence'] < 0.6)].shape[0],
            '<0.5': original_df[original_df['Match Confidence'] < 0.5].shape[0]
        }
        
        # Convert to percentages
        original_percentages = {k: (v / len(original_df)) * 100 for k, v in original_ranges.items()}
        final_percentages = {k: (v / len(final_df)) * 100 for k, v in confidence_ranges.items()}
        
        # Create bar chart
        labels = list(original_ranges.keys())
        original_values = [original_percentages[k] for k in labels]
        final_values = [final_percentages[k] for k in labels]
        
        x = range(len(labels))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        rects1 = ax.bar([i - width/2 for i in x], original_values, width, label='Original Data')
        rects2 = ax.bar([i + width/2 for i in x], final_values, width, label='Final Data')
        
        ax.set_ylabel('Percentage of Items')
        ax.set_title('Match Confidence Distribution: Original vs Final Data')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        
        # Add value labels on top of bars
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
        
        autolabel(rects1)
        autolabel(rects2)
        
        plt.tight_layout()
        plt.savefig('match_confidence_comparison.png')
        print("Generated visualization: match_confidence_comparison.png")
    except Exception as e:
        print(f"Error generating visualizations: {str(e)}")

if __name__ == "__main__":
    generate_summary_report() 