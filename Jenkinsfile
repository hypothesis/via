#!groovy

@Library('pipeline-library') _

def img

node {
    stage('build') {
        checkout(scm)
        img = buildApp(name: 'hypothesis/py_proxy')
    }

    // Run each of the stages in parallel.
    parallel failFast: true,

    "lint": {
        stage("lint") {
            testApp(image: img, runArgs: "${runArgs} -e ACCESS_CONTROL_ALLOW_ORIGIN=http://localhost:9083") {
                installDeps()
                run("make checkformatting")
                run("make checkdocstrings")
                run("make lint")
            }
        }
    },
    "tests": {
        stage("tests") {
            testApp(image: img, runArgs: "${runArgs} -e ACCESS_CONTROL_ALLOW_ORIGIN=http://localhost:9083") {
                installDeps()
                run("make test coverage")
            }
        }
    },
    onlyOnMaster {
        stage('release') {
            releaseApp(image: img)
        }
    }
}

onlyOnMaster {
    milestone()
    stage('qa deploy') {
        deployApp(image: img, app: 'py_proxy', env: 'qa')
    }

    milestone()
    stage('prod deploy') {
        input(message: "Deploy to prod?")
        milestone()
        deployApp(image: img, app: 'py_proxy', env: 'prod')
    }
}

/**
 * Install some common system dependencies.
 *
 * These are test dependencies that're need to run most of the stages above
 * (tests, lint, ...) but that aren't installed in the production Docker image.
 */
def installDeps() {
    sh "apk add build-base python3-dev"
    sh "pip3 install -q tox>=3.8.0"
}
