{
  "widgets": [

    {
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 24,
      "height": 1,
      "properties": {
        "markdown": "# 💰 Cost Attribution — by Project & Researcher\n_Custom metrics from `ResearchComputing/Costs` namespace · refreshed every 6 hours_"
      }
    },

    {
      "type": "metric",
      "x": 0,
      "y": 1,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Daily Spend by Project (USD, last 30 days)",
        "view": "timeSeries",
        "stacked": false,
        "period": 86400,
        "stat": "Sum",
        "metrics": [
          %{ for i, project in projects ~}
          [ "ResearchComputing/Costs", "DailySpend", "Project", ${jsonencode(project)} ]%{ if i < length(projects) - 1 },%{ endif }
          %{ endfor ~}
        ],
        "yAxis": { "left": { "label": "USD", "showUnits": false } },
        "legend": { "position": "bottom" }
      }
    },

    {
      "type": "metric",
      "x": 12,
      "y": 1,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Daily Spend by Researcher (USD, last 7 days)",
        "view": "bar",
        "period": 86400,
        "stat": "Sum",
        "metrics": [
          %{ for i, project in projects ~}
          [ "ResearchComputing/Costs", "DailySpend", "Project", ${jsonencode(project)} ]%{ if i < length(projects) - 1 },%{ endif }
          %{ endfor ~}
        ],
        "yAxis": { "left": { "label": "USD", "showUnits": false } }
      }
    },

    {
      "type": "text",
      "x": 0,
      "y": 7,
      "width": 24,
      "height": 1,
      "properties": {
        "markdown": "# ⚡ Spot Instance Interruptions\n_Custom metrics from `ResearchComputing/Spot` namespace · populated by EventBridge → Lambda_"
      }
    },

    {
      "type": "metric",
      "x": 0,
      "y": 8,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Spot Interruptions by Project (last 24h)",
        "view": "bar",
        "period": 3600,
        "stat": "Sum",
        "metrics": [
          %{ for i, project in projects ~}
          [ "ResearchComputing/Spot", "SpotInterruption", "Project", ${jsonencode(project)} ]%{ if i < length(projects) - 1 },%{ endif }
          %{ endfor ~}
        ],
        "yAxis": { "left": { "label": "Count", "showUnits": false } }
      }
    },

    {
      "type": "metric",
      "x": 12,
      "y": 8,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Spot Interruption Rate — 7 Day Trend",
        "view": "timeSeries",
        "period": 3600,
        "stat": "Sum",
        "metrics": [
          %{ for i, project in projects ~}
          [ "ResearchComputing/Spot", "SpotInterruption", "Project", ${jsonencode(project)} ]%{ if i < length(projects) - 1 },%{ endif }
          %{ endfor ~}
        ],
        "yAxis": { "left": { "label": "Count", "showUnits": false } }
      }
    },

    {
      "type": "text",
      "x": 0,
      "y": 14,
      "width": 24,
      "height": 1,
      "properties": {
        "markdown": "# 🖥️ EC2 Compute Utilization\n_Native metrics from `AWS/EC2` namespace · aggregated across instances_"
      }
    },

    {
      "type": "metric",
      "x": 0,
      "y": 15,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Average CPU Utilization by Project (%)",
        "view": "timeSeries",
        "period": 300,
        "stat": "Average",
        "metrics": [
          %{ for i, project in projects ~}
          [ { "expression": "SEARCH('{AWS/EC2} MetricName=\"CPUUtilization\"', 'Average', 300)", "id": ${jsonencode("cpu_${replace(project, "-", "_")}")}, "label": ${jsonencode(project)}, "visible": true } ]%{ if i < length(projects) - 1 },%{ endif }
          %{ endfor ~}
        ],
        "yAxis": { "left": { "label": "%", "min": 0, "max": 100 } },
        "annotations": {
          "horizontal": [
            { "label": "Idle threshold", "value": ${cpu_idle_threshold}, "color": "#ff7f0e" }
          ]
        }
      }
    },

    {
      "type": "metric",
      "x": 12,
      "y": 15,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "Network I/O (bytes/min)",
        "view": "timeSeries",
        "period": 300,
        "stat": "Sum",
        "metrics": [
          [ "AWS/EC2", "NetworkIn",  { "id": "net_in",  "label": "Network In",  "stat": "Sum" } ],
          [ "AWS/EC2", "NetworkOut", { "id": "net_out", "label": "Network Out", "stat": "Sum" } ]
        ],
        "yAxis": { "left": { "label": "Bytes", "showUnits": false } }
      }
    },

    {
      "type": "metric",
      "x": 0,
      "y": 21,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "EC2 Disk Read/Write (ops/min)",
        "view": "timeSeries",
        "period": 300,
        "stat": "Sum",
        "metrics": [
          [ "AWS/EC2", "DiskReadOps",  { "label": "Disk Read Ops",  "stat": "Sum" } ],
          [ "AWS/EC2", "DiskWriteOps", { "label": "Disk Write Ops", "stat": "Sum" } ]
        ],
        "yAxis": { "left": { "label": "Ops", "showUnits": false } }
      }
    },

    {
      "type": "metric",
      "x": 12,
      "y": 21,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "EC2 Instance Count (running)",
        "view": "singleValue",
        "period": 300,
        "stat": "Average",
        "metrics": [
          [ "AWS/EC2", "CPUUtilization", { "id": "m1", "visible": false } ],
          [ { "expression": "METRICS_SAMPLE_COUNT(m1)", "label": "Running Instances", "id": "instance_count" } ]
        ]
      }
    },

    {
      "type": "text",
      "x": 0,
      "y": 27,
      "width": 24,
      "height": 1,
      "properties": {
        "markdown": "# 🗄️ Storage — S3 & EFS\n_Native metrics from `AWS/S3` and `AWS/EFS` namespaces_"
      }
    }

    %{ if length(s3_buckets) > 0 },
    {
      "type": "metric",
      "x": 0,
      "y": 28,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "S3 Bucket Size (bytes)",
        "view": "timeSeries",
        "period": 86400,
        "stat": "Average",
        "metrics": [
          %{ for i, bucket in s3_buckets ~}
          [ "AWS/S3", "BucketSizeBytes", "BucketName", ${jsonencode(bucket)}, "StorageType", "StandardStorage" ]%{ if i < length(s3_buckets) - 1 },%{ endif }
          %{ endfor ~}
        ],
        "yAxis": { "left": { "label": "Bytes", "showUnits": false } }
      }
    },

    {
      "type": "metric",
      "x": 12,
      "y": 28,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "S3 Object Count",
        "view": "timeSeries",
        "period": 86400,
        "stat": "Average",
        "metrics": [
          %{ for i, bucket in s3_buckets ~}
          [ "AWS/S3", "NumberOfObjects", "BucketName", ${jsonencode(bucket)}, "StorageType", "AllStorageTypes" ]%{ if i < length(s3_buckets) - 1 },%{ endif }
          %{ endfor ~}
        ],
        "yAxis": { "left": { "label": "Objects", "showUnits": false } }
      }
    }
    %{ endif }

    %{ if length(efs_ids) > 0 },
    {
      "type": "metric",
      "x": 0,
      "y": 34,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "EFS Permitted vs Actual Throughput (MiB/s)",
        "view": "timeSeries",
        "period": 300,
        "stat": "Average",
        "metrics": [
          %{ for i, fs_id in efs_ids ~}
          [ "AWS/EFS", "PermittedThroughput", "FileSystemId", ${jsonencode(fs_id)}, { "label": ${jsonencode("${fs_id} Permitted")} } ],
          [ "AWS/EFS", "MeteredIOBytes", "FileSystemId", ${jsonencode(fs_id)}, { "label": ${jsonencode("${fs_id} Actual")}, "stat": "Sum", "period": 300 } ]%{ if i < length(efs_ids) - 1 },%{ endif }
          %{ endfor ~}
        ],
        "yAxis": { "left": { "label": "MiB/s", "showUnits": false } }
      }
    },

    {
      "type": "metric",
      "x": 12,
      "y": 34,
      "width": 12,
      "height": 6,
      "properties": {
        "title": "EFS Client Connections",
        "view": "timeSeries",
        "period": 300,
        "stat": "Average",
        "metrics": [
          %{ for i, fs_id in efs_ids ~}
          [ "AWS/EFS", "ClientConnections", "FileSystemId", ${jsonencode(fs_id)} ]%{ if i < length(efs_ids) - 1 },%{ endif }
          %{ endfor ~}
        ],
        "yAxis": { "left": { "label": "Connections", "showUnits": false } }
      }
    }
    %{ endif }

  ]
}
