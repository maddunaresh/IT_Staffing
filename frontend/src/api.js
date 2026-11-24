async function request(path, options = {}) {
  let response;

  try {
    response = await fetch(`/api${path}`, options);
  } catch {
    throw new Error("Cannot connect to the server. Check that FastAPI is running.");
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    let message = "The request could not be completed.";

    if (typeof data?.detail === "string") {
      message = data.detail;
    } else if (Array.isArray(data?.detail)) {
      message = data.detail.map((item) => item.msg).join(". ");
    }

    throw new Error(message);
  }

  return data;
}

export function login(email, password) {
  return request("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });
}

export function getCurrentUser(token) {
  return request("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export function createUser(token, userData) {
  return request("/admin/users", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(userData),
  });
}