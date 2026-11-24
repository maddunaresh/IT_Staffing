import { useState } from "react";
import SuperAdminPage from "./pages/SuperAdminPage";
import {
  Box,
  Button,
  Chip,
  CssBaseline,
  Paper,
  Stack,
  ThemeProvider,
  Typography,
  createTheme,
} from "@mui/material";

import LoginPage from "./pages/LoginPage";

const theme = createTheme({
  palette: {
    primary: {
      main: "#2563eb",
    },
    background: {
      default: "#f8fafc",
    },
    text: {
      primary: "#0f172a",
      secondary: "#64748b",
    },
  },
  typography: {
    fontFamily: '"Segoe UI", Arial, sans-serif',
    h3: {
      fontSize: "2.4rem",
      fontWeight: 750,
      letterSpacing: "-1px",
    },
    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
    },
  },
});

export default function App() {
  const [session, setSession] = useState(null);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      {!session ? (
       <LoginPage onLogin={setSession} />
) : session.role === "Super Admin" ? (
  <SuperAdminPage
    session={session}
    onSignOut={() => setSession(null)}
  />
) : (
        <Box sx={{ maxWidth: 960, mx: "auto", p: { xs: 3, md: 6 } }}>
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="center"
            spacing={2}
            sx={{ mb: 4 }}
          >
            <Typography variant="h6" fontWeight={700}>
              TalentWorkspace
            </Typography>

            <Button
              variant="outlined"
              onClick={() => setSession(null)}
            >
              Sign out
            </Button>
          </Stack>

          <Paper
            variant="outlined"
            sx={{ p: { xs: 3, md: 5 }, borderColor: "#e2e8f0" }}
          >
            <Chip label={session.role} color="primary" sx={{ mb: 2 }} />

            <Typography variant="h4" fontWeight={700} sx={{ mb: 1 }}>
              Welcome, {session.user.full_name}
            </Typography>

            <Typography color="text.secondary">
              {session.user.email}
            </Typography>

            <Typography sx={{ mt: 3 }}>
              You have successfully signed in to your{" "}
              {session.role.toLowerCase()} workspace.
            </Typography>

            <Typography color="text.secondary" sx={{ mt: 1 }}>
              Your module screens will be added here next.
            </Typography>
          </Paper>
        </Box>
      )}
    </ThemeProvider>
  );
}