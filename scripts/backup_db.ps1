# Powershell script to automate database backups (Module 9)

$ErrorActionPreference = "Stop"

# Create backup directory
$BackupDir = Join-Path (Get-Location) "data\backups"
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Load environment variables from .env
$EnvFile = Join-Path (Get-Location) ".env"
$DbUrl = "sqlite:///./data/orzen_dev.db"  # default

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^\s*DATABASE_URL\s*=\s*(.+)$") {
            $DbUrl = $Matches[1].Trim()
        }
    }
}

Write-Host "Database URL resolved: $DbUrl" -ForegroundColor Cyan

if ($DbUrl.StartsWith("sqlite:///")) {
    # SQLite Backup
    # Extract path from URL (remove sqlite:///)
    $RawPath = $DbUrl.Substring(10)
    # Handle relative paths
    if (-not [System.IO.Path]::IsPathRooted($RawPath)) {
        $RawPath = Join-Path (Get-Location) $RawPath
    }
    
    $BackupFile = Join-Path $BackupDir "orzen_dev_backup_$Timestamp.db"
    
    if (Test-Path $RawPath) {
        Write-Host "Backing up SQLite database from: $RawPath" -ForegroundColor Yellow
        Copy-Item -Path $RawPath -Destination $BackupFile -Force
        Write-Host "SQLite backup completed: $BackupFile" -ForegroundColor Green
    } else {
        Write-Error "SQLite database file not found at: $RawPath"
    }
}
elseif ($DbUrl.Contains("postgresql")) {
    # PostgreSQL Backup
    Write-Host "Backing up PostgreSQL database..." -ForegroundColor Yellow
    # Extract details using regex
    # format: postgresql+psycopg2://user:password@host:port/dbname
    if ($DbUrl -match "postgresql(?:\+psycopg2)?://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/([^?]+)") {
        $User = $Matches[1]
        $Password = $Matches[2]
        $Host = $Matches[3]
        $Port = if ($Matches[4]) { $Matches[4] } else { "5432" }
        $DbName = $Matches[5]
        
        $BackupFile = Join-Path $BackupDir "$DbName`_backup_$Timestamp.sql"
        
        # Set PG PASSWORD env
        $env:PGPASSWORD = $Password
        
        # Call pg_dump
        & pg_dump -h $Host -p $Port -U $User -F p -b -v -f $BackupFile $DbName
        
        # Clear env password
        Remove-Item Env:\PGPASSWORD
        
        Write-Host "PostgreSQL backup completed: $BackupFile" -ForegroundColor Green
    } else {
        Write-Error "Invalid PostgreSQL connection string format in .env"
    }
}
else {
    Write-Error "Unsupported database type for backups: $DbUrl"
}
