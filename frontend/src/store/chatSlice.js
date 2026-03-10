import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  sessionId: crypto.randomUUID(),
  messages: [],
  status: "idle", // idle | loading
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addMessage(state, action) {
      state.messages.push(action.payload);
    },
    setStatus(state, action) {
      state.status = action.payload;
    },
    resetChat(state) {
      state.sessionId = crypto.randomUUID();
      state.messages = [];
      state.status = "idle";
    },
  },
});

export const { addMessage, setStatus, resetChat } = chatSlice.actions;
export default chatSlice.reducer;
