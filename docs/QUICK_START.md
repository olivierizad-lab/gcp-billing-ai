# Quick Start - Course Deployment

Perfect for temporary/course deployments. Simple, secure, and easy to clean up!

## 🚀 Deploy (3 Steps)

```bash
# 1. Set your project
export PROJECT_ID="your-project-id"

# 2. Deploy
cd web/deploy
./deploy-simple-iap.sh

# 3. Done! You'll get URLs like:
#    API: https://agent-engine-api-xxxxx-uc.a.run.app
#    UI:  https://agent-engine-ui-xxxxx-uc.a.run.app
```

## 🔐 Access

Users will authenticate with Google accounts when accessing the URLs. By default, all authenticated users can access.

## 🧹 Cleanup (When Course Ends)

```bash
cd web/deploy
export PROJECT_ID="your-project-id"
./cleanup.sh
```

That's it! All resources deleted.

## 📋 What You Get

- ✅ **Secure** - IAP authentication
- ✅ **HTTPS** - Automatic SSL
- ✅ **No DNS** - Uses Cloud Run URLs
- ✅ **Simple** - One script to deploy, one to clean up
- ✅ **Cheap** - Pay only for what you use

## 💡 Tips

1. **Share URLs** - Just share the UI URL with your team/instructor
2. **Grant Access** - Control who can access via IAM policies
3. **Monitor Costs** - Check Cloud Console billing dashboard
4. **Clean Up** - Run cleanup script when done to avoid charges

## 📚 More Info

- [README-SIMPLE.md](./README-SIMPLE.md) - Full documentation
- [cleanup.sh](./cleanup.sh) - Cleanup script details

