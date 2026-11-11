# docker build -t m12-travelz:dev .
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY src/Travelz/Travelz.csproj src/Travelz/
RUN dotnet restore src/Travelz/Travelz.csproj
COPY src/Travelz/ src/Travelz/
RUN dotnet publish src/Travelz/Travelz.csproj -c Release --no-restore -p:UseAppHost=false -o /out
FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /out/ ./
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
ENTRYPOINT ["dotnet", "Travelz.dll"]
