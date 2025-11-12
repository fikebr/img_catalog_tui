# Feature: Move ImageSet(s) to Target Folder

This feature allows users to move one or more `ImageSets` to a selected target folder via the web interface.

---

## Implementation Steps

1. **Add Method to `ImageSet` Class**

   * Implement a method that enables moving an `ImageSet` instance to a different folder.
   * Ensure all associated metadata and references are updated accordingly.
   * input is new folder
   * output is the full os path to the new folder

2. **Add API Route and View**

   * Create an API endpoint that handles the folder move action.
   * The route should accept an `ImageSet` ID and the target folder ID as parameters.
   * Return success/failure responses in JSON format.

3. **Create HTML Route, View, and Template**

   * Develop a dialog form that allows the user to select a new folder for the chosen `ImageSet`.
   * The dialog should provide a clear list or dropdown of available folders.
   * Include client-side validation and user feedback messages.

---

## UI Integration

4. **ImageSet Page Enhancements**

   * Add a button labeled **“Move ImageSet”** on each ImageSet’s detail page.
   * Clicking this button should open the “Move ImageSet” dialog form.

5. **Folder Page Enhancements (Per ImageSet)**

   * On the folder page, add a **“Move”** button to each ImageSet card.
   * This button should allow the user to move that specific ImageSet to another folder.

6. **Folder Page Enhancements (Bulk Actions)**

   * Add a **“Move All”** button that moves all ImageSets in the current folder to a target folder.
   * After completion, redirect or refresh the view to display the target folder’s contents.

7. **Folder Page Enhancements (By Status)**

   * On each **status count card**, add a **“Move”** button that moves all ImageSets with that status to a selected folder.
   * The user should be prompted to confirm or select the destination folder before the operation proceeds.




