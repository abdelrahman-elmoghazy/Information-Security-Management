#!/bin/bash

# Check if the log file exists
if [ ! -f "apache_logs" ]; then
  echo "Error: apache_logs not found!"
  exit 1
fi

# Create a temporary directory for intermediate files
mkdir -p tmp
rm -f tmp/*

# 1. Request Counts
total_requests=$(wc -l < apache_logs)
get_requests=$(grep -c '"GET ' apache_logs)
post_requests=$(grep -c '"POST ' apache_logs)

echo "1. Request Counts:"
echo "Total Requests: $total_requests"
echo "GET Requests: $get_requests"
echo "POST Requests: $post_requests"
echo

# 2. Unique IP Addresses
awk '{print $1}' apache_logs | sort | uniq > tmp/unique_ips.txt
unique_ip_count=$(wc -l < tmp/unique_ips.txt)

echo "2. Unique IP Addresses:"
echo "Total Unique IPs: $unique_ip_count"
echo "IP | GET Requests | POST Requests"
echo "--------------------------------"
while read -r ip; do
  get_count=$(grep "$ip" apache_logs | grep -c '"GET ')
  post_count=$(grep "$ip" apache_logs | grep -c '"POST ')
  echo "$ip | $get_count | $post_count"
done < tmp/unique_ips.txt > tmp/ip_requests.txt
cat tmp/ip_requests.txt
echo

# 3. Failure Requests
failure_requests=$(awk '$9 ~ /^[4-5][0-9][0-9]$/ {count++} END {print count+0}' apache_logs)
failure_percentage=$(echo "scale=2; ($failure_requests / $total_requests) * 100" | bc)

echo "3. Failure Requests:"
echo "Failed Requests (4xx/5xx): $failure_requests"
echo "Failure Percentage: $failure_percentage%"
echo

# 4. Most Active User
top_ip=$(awk '{print $1}' apache_logs | sort | uniq -c | sort -nr | head -1 | awk '{print $2}')
top_ip_requests=$(awk '{print $1}' apache_logs | sort | uniq -c | sort -nr | head -1 | awk '{print $1}')

echo "4. Most Active User:"
echo "Most Active IP: $top_ip ($top_ip_requests requests)"
echo

# 5. Daily Request Averages
awk -F'[' '{split($2, date, ":"); print date[1]}' apache_logs | sort | uniq -c > tmp/daily_counts.txt
total_days=$(wc -l < tmp/daily_counts.txt)
daily_avg=$(echo "scale=2; $total_requests / $total_days" | bc)

echo "5. Daily Request Averages:"
echo "Total Days: $total_days"
echo "Average Requests per Day: $daily_avg"
echo

# 6. Failure Analysis
awk '$9 ~ /^[4-5][0-9][0-9]$/ {split($4, date, ":"); print date[1]}' apache_logs | sort | uniq -c | sort -nr > tmp/failure_days.txt

echo "6. Days with Most Failures:"
cat tmp/failure_days.txt
echo

# 7. Requests by Hour
awk -F: '{split($4, time, ":"); print time[2]}' apache_logs | sort | uniq -c | sort -n > tmp/hourly_counts.txt

echo "7. Requests by Hour:"
cat tmp/hourly_counts.txt
echo

# 8. Status Codes Breakdown
awk '{print $9}' apache_logs | sort | uniq -c | sort -nr > tmp/status_codes.txt

echo "8. Status Codes Breakdown:"
cat tmp/status_codes.txt
echo

# 9. Most Active User by Method
top_get_ip=$(awk '/"GET / {print $1}' apache_logs | sort | uniq -c | sort -nr | head -1 | awk '{print $2 " (" $1 " requests)"}')
top_post_ip=$(awk '/"POST / {print $1}' apache_logs | sort | uniq -c | sort -nr | head -1 | awk '{print $2 " (" $1 " requests)"}')

echo "9. Most Active User by Method:"
echo "Most Active GET IP: $top_get_ip"
echo "Most Active POST IP: $top_post_ip"
echo

# 10. Patterns in Failure Requests
awk '$9 ~ /^[4-5][0-9][0-9]$/ {split($4, time, ":"); print time[2]}' apache_logs | sort | uniq -c | sort -nr > tmp/failure_hours.txt

echo "10. Failure Requests by Hour:"
cat tmp/failure_hours.txt
echo

# 11. Request Trends
peak_hour=$(awk -F: '{split($4, time, ":"); print time[2]}' apache_logs | sort | uniq -c | sort -nr | head -1 | awk '{print $2 " (" $1 " requests)"}')
low_hour=$(awk -F: '{split($4, time, ":"); print time[2]}' apache_logs | sort | uniq -c | sort -n | head -1 | awk '{print $2 " (" $1 " requests)"}')

echo "11. Request Trends:"
echo "Peak Hour: $peak_hour"
echo "Low Hour: $low_hour"
echo

# 12. Analysis Threatens
echo "12. Analysis Suggestions:"
if [ $(echo "$failure_percentage > 5" | bc) -eq 1 ]; then
  echo "- High failure rate ($failure_percentage%) detected. Check server logs for 4xx/5xx errors. Possible causes: broken links (404), server overload (503), or authentication issues (401)."
fi
if [ -s tmp/failure_hours.txt ]; then
  top_failure_hour=$(head -1 tmp/failure_hours.txt | awk '{print $2 " (" $1 " failures)"}')
  echo "- Most failures occur at hour $top_failure_hour. Check for server load or scheduled tasks during this time."
fi
if [ -s tmp/failure_days.txt ]; then
  top_failure_day=$(head -1 tmp/failure_days.txt | awk '{print $2 " (" $1 " failures)"}')
  echo "- Most failures on $top_failure_day. Review server events or deployments on this day."
fi
if [ $top_ip_requests -gt 1000 ]; then
  echo "- IP $top_ip made $top_ip_requests requests, which is unusually high. Investigate for potential bot activity or DDoS."
fi
echo "- Schedule maintenance during low-traffic hours (e.g., $low_hour) to minimize user impact."
echo "- Consider load balancing or caching if peak hour ($peak_hour) causes performance issues."
echo "- Monitor status codes regularly and set up alerts for spikes in 5xx errors."

# Clean up temporary files
rm -rf tmp
