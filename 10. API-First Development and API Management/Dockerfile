# Run from Module 10 root: docker build -t m10-products:dev .
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY src/ProductsApi/ProductsApi.csproj src/ProductsApi/
RUN dotnet restore src/ProductsApi/ProductsApi.csproj
COPY src/ProductsApi/ src/ProductsApi/
RUN dotnet publish src/ProductsApi/ProductsApi.csproj -c Release -o /out --no-restore -p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /out/ ./
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
# No fixed USER: restricted OpenShift SCC can inject an arbitrary non-root UID.
# This app does not write to /app or require root.
ENTRYPOINT ["dotnet", "ProductsApi.dll"]
