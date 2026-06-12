package ci

# Disallow usage of privileged Dockerfile instructions such as USER root
# This is a simple example policy; expand as needed.

deny[msg] {
    input.kind == "Dockerfile"
    re_match("(?i)USER\s+root", input.content)
    msg := "Dockerfile must not use USER root"
}

# Ensure that any environment variable set in .env files does not contain obvious secrets

deny[msg] {
    input.kind == "EnvFile"
    re_match("(?i)PASSWORD\s*=\s*.+", input.content)
    msg := "Env file contains a PASSWORD entry; use Vault instead"
}
