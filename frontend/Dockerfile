# using NodeJS to build React app
FROM node:lts AS development

# setting working directory
WORKDIR /app

# copy dependencies
COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json

# same as npm install
RUN npm ci

# copy the source code
COPY . /app

# continuous integration (CI) environment
# listen on port 3000
ENV CI=true
ENV PORT=3000

CMD [ "npm", "start" ]