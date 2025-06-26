"""
Generate detailed reports of market predictions and outcomes.
This script provides auditability and transparency for market results.
"""

import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv
from app import db
from app.models import Market, Prediction, User

# Load environment variables
load_dotenv()

def get_market_predictions(market_id):
    """
    Retrieve all predictions for a specific market.
    Returns a list of dictionaries with prediction details.
    """
    market = Market.query.get(market_id)
    if not market:
        return None, "Market not found"
    
    if not market.resolved:
        return None, "Market not resolved yet"
    
    predictions = Prediction.query.filter_by(market_id=market_id).all()
    
    report = {
        'market': {
            'id': market.id,
            'title': market.title,
            'resolution_date': market.resolution_date.strftime('%Y-%m-%d'),
            'resolved_outcome': market.resolved_outcome,
            'resolved_at': market.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if market.resolved_at else None,
            'integrity_hash': market.integrity_hash
        },
        'predictions': []
    }
    
    for prediction in predictions:
        user = User.query.get(prediction.user_id)
        report['predictions'].append({
            'user': {
                'id': user.id,
                'username': user.username,
                'reliability_index': user.reliability_index
            },
            'prediction': {
                'id': prediction.id,
                'prediction': prediction.prediction,
                'points_staked': prediction.points_staked,
                'staked_from_lb': prediction.staked_from_lb,
                'points_won': prediction.points_won,
                'created_at': prediction.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    return report, None

def generate_csv_report(market_id, output_dir='reports'):
    """
    Generate a CSV report for a market's predictions.
    Returns the path to the generated CSV file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    report_data, error = get_market_predictions(market_id)
    if error:
        return None, error
    
    market = report_data['market']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"market_{market_id}_report_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow([
            'Market ID', 'Market Title', 'Resolution Date', 'Resolved Outcome',
            'User ID', 'Username', 'Reliability Index',
            'Prediction', 'Points Staked', 'Staked from LB',
            'Points Won', 'Prediction Time', 'Integrity Hash'
        ])
        
        # Write market data row
        writer.writerow([
            market['id'], market['title'], market['resolution_date'], market['resolved_outcome'],
            '', '', '', '', '', '', '', '', market['integrity_hash']
        ])
        
        # Write prediction rows
        for pred in report_data['predictions']:
            user = pred['user']
            pred_data = pred['prediction']
            writer.writerow([
                '', '', '', '',
                user['id'], user['username'], user['reliability_index'],
                pred_data['prediction'], pred_data['points_staked'], pred_data['staked_from_lb'],
                pred_data['points_won'], pred_data['created_at'], ''
            ])
    
    return filepath, None

def generate_json_report(market_id, output_dir='reports'):
    """
    Generate a JSON report for a market's predictions.
    Returns the path to the generated JSON file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    report_data, error = get_market_predictions(market_id)
    if error:
        return None, error
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"market_{market_id}_report_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as jsonfile:
        json.dump(report_data, jsonfile, indent=2)
    
    return filepath, None

def main():
    """Main function to handle command-line arguments and generate reports"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate market prediction reports')
    parser.add_argument('market_id', type=int, help='ID of the market to generate report for')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                       help='Output format (default: csv)')
    
    args = parser.parse_args()
    
    if args.format == 'csv':
        filepath, error = generate_csv_report(args.market_id)
    else:
        filepath, error = generate_json_report(args.market_id)
    
    if error:
        print(f"Error: {error}")
        return 1
    
    print(f"Report generated successfully: {filepath}")
    return 0

if __name__ == "__main__":
    exit(main())
