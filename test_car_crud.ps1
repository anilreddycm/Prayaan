#!/usr/bin/env powershell
<#
.SYNOPSIS
    Car CRUD API Test Script - Quick demo of all operations
.DESCRIPTION
    Demonstrates CREATE, READ, UPDATE, DELETE operations via curl on the Car API
.PARAMETER Username
    Admin username (default: admin)
.PARAMETER Password
    Admin password (default: will prompt)
.PARAMETER BaseUrl
    Base URL of the server (default: http://127.0.0.1:8000)
.EXAMPLE
    .\test_car_crud.ps1 -Username admin -Password mypassword
#>
param(
    [string]$Username = "admin",
    [string]$Password,
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

if (-not $Password) {
    $Password = Read-Host "Enter password for user '$Username'" -AsSecureString
    $Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($Password))
}

$creds = "$($Username):$($Password)"
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($creds))

Write-Host "`n" -ForegroundColor Cyan
Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🚗 Car Management API - CRUD Demo 🚗    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan

function Make-ApiCall {
    param(
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body = $null,
        [string]$Description = ""
    )
    
    $url = "$BaseUrl$Endpoint"
    
    Write-Host "`n┌─ $Method $Endpoint" -ForegroundColor Magenta
    if ($Description) {
        Write-Host "│  📝 $Description"
    }
    Write-Host "│"
    
    try {
        $params = @{
            Uri = $url
            Method = $Method
            Headers = @{ 
                "Authorization" = "Basic $encoded"
                "Content-Type" = "application/json"
                "User-Agent" = "PowerShell-CurlDemo/1.0"
            }
            ErrorAction = "Stop"
            TimeoutSec = 10
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json -Depth 10
        }
        
        $response = Invoke-RestMethod @params
        
        Write-Host "│  ✅ Success (Status: OK)" -ForegroundColor Green
        Write-Host "│" 
        Write-Host "│  Response:" 
        if ($response -is [System.Collections.IEnumerable] -and $response -isnot [string]) {
            Write-Host "│  Count: $($response.Count) items"
            if ($response.Count -le 3) {
                $response | ForEach-Object { 
                    Write-Host "│    - ID: $($_.id), Category: $($_.category)"
                }
            }
        } else {
            Write-Host "│    ID: $($response.id)"
            Write-Host "│    Category: $($response.category)"
            Write-Host "│    Registration: $($response.registration_number)"
            Write-Host "│    Price: ₹$($response.price)"
        }
        Write-Host "└─"
        return $response
    }
    catch {
        Write-Host "│  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "└─"
        return $null
    }
}

# 1️⃣ READ - List all cars
Write-Host "`n[Step 1/5] Listing all cars" -ForegroundColor Yellow
$allCars = Make-ApiCall -Method GET -Endpoint "/api/cars/" -Description "Get list of all available cars"

# 2️⃣ CREATE - Add a new car
Write-Host "`n[Step 2/5] Creating a new car" -ForegroundColor Yellow
$newCarData = @{
    category = "Honda City"
    ac_type = "AC"
    total_cars = 2
    registration_number = "DL-CURL-$(Get-Date -Format 'hhmmss')"
    price = 5800
    price_per_hour = 220
    price_per_km = 14
    fuel_consumption = "petrol"
    status = "available"
}
$newCar = Make-ApiCall -Method POST -Endpoint "/api/cars/" -Body $newCarData -Description "Add new Honda City to fleet"

if ($newCar) {
    $carId = $newCar.id
    
    # 3️⃣ READ - Get the created car details
    Write-Host "`n[Step 3/5] Retrieving car details" -ForegroundColor Yellow
    $carDetail = Make-ApiCall -Method GET -Endpoint "/api/cars/$carId/" -Description "Fetch details of newly created car"
    
    # 4️⃣ UPDATE - Modify the car
    Write-Host "`n[Step 4/5] Updating car" -ForegroundColor Yellow
    $updateData = @{
        price = 6000
        total_cars = 3
        price_per_hour = 250
    }
    $updated = Make-ApiCall -Method PUT -Endpoint "/api/cars/$carId/" -Body $updateData -Description "Update price and availability"
    
    # 5️⃣ DELETE - Remove the car
    Write-Host "`n[Step 5/5] Deleting car" -ForegroundColor Yellow
    Make-ApiCall -Method DELETE -Endpoint "/api/cars/$carId/" -Description "Remove the test car from database"
}

Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║        ✅ CRUD Demo Complete! ✅           ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n📖 For more information, see: CURL_API_GUIDE.md" -ForegroundColor Cyan
