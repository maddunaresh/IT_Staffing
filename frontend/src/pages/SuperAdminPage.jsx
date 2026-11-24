import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { createUser } from "../api";

const emptyForm = {
  full_name: "",
  email: "",
  password: "",
  role: "",
};

const roleOptions = [
  { label: "Manager", value: "Manager" },
  { label: "Recruiter", value: "Recruiter" },
  { label: "Marketer", value: "Bench Sales Marketer" },
];

export default function SuperAdminPage({ session, onSignOut }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function openDialog() {
    setForm(emptyForm);
    setError("");
    setSuccess("");
    setOpen(true);
  }

  function closeDialog() {
  if (busy) return;

  setOpen(false);
  setForm(emptyForm);
  setError("");
}

function handleDialogClose(_event, reason) {
  if (reason === "backdropClick" || busy) return;

  closeDialog();
}

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (busy) return;

    const fullName = form.full_name.trim();

    if (!fullName) {
      setError("Enter the user's full name.");
      return;
    }

    setError("");
    setBusy(true);

    try {
      const user = await createUser(session.token, {
        ...form,
        full_name: fullName,
        email: form.email.trim(),
      });

      const roleLabel = roleOptions.find(
        (option) => option.value === form.role
      )?.label;

      setSuccess(
        `${user.full_name}'s ${roleLabel} account was created. ` +
        `They can now sign in with ${user.email}.`
      );
      setForm(emptyForm);
      setOpen(false);
    } catch (err) {
      setError(err.message || "Could not create the account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box component="main" sx={{ maxWidth: 1120, mx: "auto", p: { xs: 2, md: 5 } }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "stretch", sm: "center" }}
        spacing={2}
        sx={{ mb: 3 }}
      >
        <Typography component="h1" variant="h4" fontWeight={700}>
          User Management
        </Typography>

        <Stack direction="row" spacing={1} justifyContent="flex-end">
          <Button onClick={onSignOut}>Sign out</Button>
          <Button variant="contained" onClick={openDialog}>
            Create User
          </Button>
        </Stack>
      </Stack>

      {success && (
        <Alert severity="success" onClose={() => setSuccess("")}>
          {success}
        </Alert>
      )}

      <Dialog
        open={open}
        onClose={handleDialogClose}
        fullWidth
        maxWidth="xs"
        aria-labelledby="create-user-title"
      >
        <Box component="form" onSubmit={handleSubmit} aria-busy={busy}>
          <DialogTitle id="create-user-title">Create User</DialogTitle>

          <DialogContent>
            <Stack spacing={2} sx={{ pt: 1 }}>
              {error && <Alert severity="error">{error}</Alert>}

              <TextField
                autoFocus
                required
                name="full_name"
                label="Full name"
                value={form.full_name}
                onChange={updateField}
                disabled={busy}
              />

              <TextField
                required
                name="email"
                label="Work email"
                type="email"
                value={form.email}
                onChange={updateField}
                disabled={busy}
              />

              <TextField
                required
                name="password"
                label="Password"
                type="password"
                autoComplete="new-password"
                value={form.password}
                onChange={updateField}
                disabled={busy}
                helperText="Use at least 10 characters."
                slotProps={{ htmlInput: { minLength: 10 } }}
              />

              <TextField
                select
                required
                name="role"
                label="Role"
                value={form.role}
                onChange={updateField}
                disabled={busy}
              >
                {roleOptions.map(({ label, value }) => (
                  <MenuItem key={value} value={value}>
                    {label}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>
          </DialogContent>

          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button type="button" onClick={closeDialog} disabled={busy}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={busy || !form.role}
            >
              {busy ? "Creating…" : "Create User"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Box>
  );
}