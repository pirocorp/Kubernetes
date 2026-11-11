# Execute from the root of Module 11: docker build -t m11-orderplacement:dev .
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS builder
WORKDIR /src
COPY src/OrderPlacementApi/OrderPlacementApi.csproj src/OrderPlacementApi/
RUN dotnet restore src/OrderPlacementApi/OrderPlacementApi.csproj
COPY src/OrderPlacementApi/ src/OrderPlacementApi/
RUN dotnet publish src/OrderPlacementApi/OrderPlacementApi.csproj -c Release --no-restore -p:UseAppHost=false -o /out

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=builder /out/ ./
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
# No privileged ports, no writes under /app. OpenShift may inject an arbitrary UID.
ENTRYPOINT ["dotnet", "OrderPlacementApi.dll"]
