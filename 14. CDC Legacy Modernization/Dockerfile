FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY src/RetailModernization/RetailModernization.csproj src/RetailModernization/
RUN dotnet restore src/RetailModernization/RetailModernization.csproj
COPY src/RetailModernization/ src/RetailModernization/
RUN dotnet publish src/RetailModernization/RetailModernization.csproj -c Release --no-restore -p:UseAppHost=false -o /out

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /out ./
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
USER 10001
ENTRYPOINT ["dotnet","RetailModernization.dll"]
