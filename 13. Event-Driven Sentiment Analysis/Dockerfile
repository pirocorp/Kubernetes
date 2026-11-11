FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY src/GlobexReviews/GlobexReviews.csproj src/GlobexReviews/
RUN dotnet restore src/GlobexReviews/GlobexReviews.csproj
COPY src/GlobexReviews/ src/GlobexReviews/
RUN dotnet publish src/GlobexReviews/GlobexReviews.csproj -c Release --no-restore -p:UseAppHost=false -o /out

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /out/ ./
ENV ASPNETCORE_URLS=http://+:8080 REVIEWS_MODE=local
USER 10001
EXPOSE 8080
ENTRYPOINT ["dotnet", "GlobexReviews.dll"]
